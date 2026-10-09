"""Core behavior: status rules, storage, ranking, batching, sources, documents, and the UI server's guards.
Run with: python3 -m unittest discover -s tests   (no network needed)"""
import json
import pathlib
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from applyanything import batch, config, docs, insights, pipeline, platforms, rank  # noqa: E402
from applyanything.db import DB, advance  # noqa: E402
from applyanything.sources import devpost  # noqa: E402

NOW = 1_790_000_000
CFG = config.merge(config.DEFAULTS, {
    "rank": {"reach": ["BigCo"], "competitive": ["MidCo"], "accessible": ["SmallCo"],
             "fit": ["software engineer", "ml"], "far": ["ios"], "ineligible": ["phd"], "questions": False},
    "eligibility": {"requires_citizenship": ["DefenseCo"], "needs_sponsorship": True, "no_sponsorship": ["NoVisaCo"],
                    "countries": ["US"]},
    "batch": {"size": 2, "per_org": 1},
})


def opp(i, org, title="Software Engineer Intern", url="https://job-boards.greenhouse.io/x/jobs/1", **kw):
    return {"id": i, "source": "test", "org": org, "title": title, "kind": kw.pop("kind", "internship"),
            "category": "", "locations": kw.pop("locations", ["New York, NY"]), "url": url,
            "posted_at": kw.pop("posted_at", NOW - 86400), "deadline": kw.pop("deadline", None), "extra": {}, **kw}


class TempDB(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = DB(pathlib.Path(self.dir.name) / "t.db")

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()


class StatusRules(unittest.TestCase):
    def test_forward_only(self):
        self.assertEqual(advance("", "applied"), "applied")
        self.assertEqual(advance("interview", "applied"), "interview")
        self.assertEqual(advance("applied", "assessment"), "assessment")

    def test_side_outcomes_from_anywhere(self):
        self.assertEqual(advance("interview", "rejected"), "rejected")
        self.assertEqual(advance("", "waitlisted"), "waitlisted")

    def test_reopen_after_waitlist_but_not_after_rejection(self):
        self.assertEqual(advance("waitlisted", "offer"), "offer")
        self.assertEqual(advance("rejected", "applied"), "rejected")


class Storage(TempDB):
    def test_upsert_and_deactivate(self):
        added, updated = self.db.upsert([opp("a", "A"), opp("b", "B")], NOW)
        self.assertEqual((sorted(added), updated), (["a", "b"], 0))
        added, updated = self.db.upsert([opp("a", "A", title="Renamed")], NOW + 10)
        self.assertEqual((added, updated), ([], 1))
        self.assertEqual(self.db.deactivate_missing("test", {"a"}), ["b"])
        rows = {r["id"]: r for r in self.db.rows()}
        self.assertEqual(rows["a"]["title"], "Renamed")
        self.assertEqual((rows["a"]["active"], rows["b"]["active"]), (1, 0))

    def test_events_dedupe_and_advance(self):
        self.db.upsert([opp("a", "A")], NOW)
        self.assertEqual(self.db.add_event("a", NOW, "applied", "received", msg="m1"), (True, "applied"))
        self.assertEqual(self.db.add_event("a", NOW, "applied", "received", msg="m1"), (False, None))
        self.db.add_event("a", NOW + 86400, "interview", "call", msg="m2")
        self.db.add_event("a", NOW + 2 * 86400, "applied", "late confirmation", msg="m3")
        r = self.db.get("a")
        self.assertEqual(r["status"], "interview")
        self.assertEqual(r["applied_at"], NOW)
        self.assertEqual(len(r["events"]), 3)

    def test_answers_merge_and_remove(self):
        self.db.upsert([opp("a", "A")], NOW)
        self.db.set_app("a", answers={"GPA": "blank", "Grad": "May 2028"})
        self.db.set_app("a", answers={"GPA": ""})
        self.assertEqual(self.db.get("a")["answers"], {"Grad": "May 2028"})

    def test_find(self):
        self.db.upsert([opp("gh-acme-1", "Acme"), opp("gh-acme-2", "Acme"), opp("lever-zed-1", "Zed")], NOW)
        self.assertEqual(self.db.find("lever"), "lever-zed-1")
        self.assertEqual(self.db.find("Zed"), "lever-zed-1")
        self.assertIsNone(self.db.find("gh-acme"))


class Ranking(unittest.TestCase):
    def rank1(self, **kw):
        r = opp("x", kw.pop("org", "Unlisted"), **kw)
        return rank.rank([r], CFG, fetch_questions=False, now=NOW)[0]

    def test_tiers_and_fit(self):
        self.assertEqual(self.rank1(org="BigCo")["tier"], "reach")
        self.assertEqual(self.rank1(org="Unlisted")["tier"], "solid")
        far = self.rank1(org="MidCo", title="iOS Engineer Intern")
        fit = self.rank1(org="MidCo")
        self.assertGreater(far["effort"], fit["effort"])

    def test_flags(self):
        self.assertIn("citizen", self.rank1(org="DefenseCo")["flags"])
        self.assertIn("no-sponsor", self.rank1(org="NoVisaCo")["flags"])
        self.assertIn("location", self.rank1(locations=["London, UK"])["flags"])
        self.assertNotIn("location", self.rank1(locations=["Remote"])["flags"])
        self.assertIn("closed", self.rank1(deadline=NOW - 10)["flags"])
        self.assertEqual(self.rank1(title="PhD Research Intern")["tier"], "ineligible")

    def test_location_filter_skips_events(self):
        r = self.rank1(kind="hackathon", locations=["Some Venue Hall"])
        self.assertNotIn("location", r["flags"])

    def test_platforms(self):
        self.assertEqual(platforms.detect("https://jobs.ashbyhq.com/x/1")[:2], ("Ashby", "agent"))
        self.assertEqual(platforms.detect("https://x.wd1.myworkdayjobs.com/en-US/y")[:2], ("Workday", "account"))
        self.assertEqual(platforms.detect("https://lu.ma/abc")[:2], ("Luma", "agent"))
        self.assertEqual(platforms.detect("https://careers.example.com/1")[1], "check")


class Batching(TempDB):
    def seed(self, rows):
        self.db.upsert(rows, NOW)
        rank.rank(rows, CFG, fetch_questions=False, now=NOW)
        self.db.save_rank(rows)

    def test_prestige_order_one_per_org_and_flags_out(self):
        self.seed([opp("r1", "BigCo"), opp("r2", "BigCo", title="ML Engineer Intern"), opp("c1", "MidCo"),
                   opp("s1", "SmallCo"), opp("d1", "DefenseCo"), opp("u1", "Unlisted")])
        plan, s = batch.build(self.db.rows(), CFG, now=NOW)
        ids = [i for b in plan["batches"] for i in b["ids"]]
        self.assertIn(ids[0], {"r1", "r2"})                         # reach tier first
        self.assertEqual(sum(i.startswith("r") for i in ids), 1)    # one per org
        self.assertNotIn("d1", ids)                                  # citizenship flag
        self.assertEqual(ids.index("c1") < ids.index("u1") < ids.index("s1"), True)
        self.assertEqual(s["repeats"], 1)

    def test_rounds_freeze_and_started_batches_are_kept(self):
        self.seed([opp(f"o{k}", f"Org{k}") for k in range(6)])
        plan, _ = batch.build(self.db.rows(), CFG, now=NOW)
        first = plan["batches"][0]["ids"]
        self.db.set_app(first[0], status="applied")
        self.db.set_app("o5", round=1)
        self.seed([opp("new", "BigCo")])
        plan2, s = batch.build(self.db.rows(), CFG, plan, now=NOW)
        self.assertEqual(plan2["batches"][0], {"ids": ["o5"], "round": 1, "mins": 4, "n": 1})
        self.assertEqual(plan2["batches"][1]["ids"], [i for i in first if i != "o5"])
        self.assertIn("new", plan2["batches"][2]["ids"])             # new reach role leads the rebuilt ones
        self.assertEqual((s["rounds"], s["kept"]), (1, 1))

    def test_deadline_mode(self):
        self.seed([opp("late", "A", kind="hackathon", deadline=NOW + 9 * 86400),
                   opp("soon", "B", kind="hackathon", deadline=NOW + 86400), opp("none", "C")])
        plan, _ = batch.build(self.db.rows(), CFG, mode="deadline", now=NOW)
        self.assertEqual([i for b in plan["batches"] for i in b["ids"]], ["soon", "late", "none"])

    def test_scoreboard_fast_rejection_and_auto_assessment(self):
        self.seed([opp("a", "A"), opp("b", "B")])
        self.db.set_app("a", iteration=1)
        self.db.add_event("a", NOW, "applied", msg="1")
        self.db.add_event("a", NOW + 2 * 86400, "rejected", msg="2")
        self.db.add_event("b", NOW, "applied", msg="3")
        self.db.add_event("b", NOW + 600, "assessment", msg="4")
        sb = {s["iteration"]: s for s in insights.scoreboard(self.db.rows(), self.db.events())}
        self.assertEqual((sb[1]["fastRejected"], sb[1]["submitted"]), (1, 1))
        self.assertEqual((sb[0]["assessment"], sb[0]["autoAssessment"]), (1, 1))


class Sources(unittest.TestCase):
    def test_devpost_dates(self):
        end = lambda s: time.strftime("%Y-%m-%d", time.localtime(devpost.end_date(s)))
        self.assertEqual(end("Aug 31 - Oct 23, 2026"), "2026-10-23")
        self.assertEqual(end("Oct 01 - 10, 2026"), "2026-10-10")
        self.assertEqual(end("Aug 23, 2026 - Jan 02, 2027"), "2027-01-02")
        self.assertIsNone(devpost.end_date("TBD"))

    def test_guess_kind(self):
        self.assertEqual(pipeline.guess_kind("Open Climate Hackathon"), "hackathon")
        self.assertEqual(pipeline.guess_kind("Summer Research Fellowship"), "fellowship")
        self.assertEqual(pipeline.guess_kind("SWE Intern, Summer 2027"), "internship")
        self.assertEqual(pipeline.guess_kind("Staff Engineer"), "job")

    def test_add_without_lookup(self):
        with tempfile.TemporaryDirectory() as d:
            db = DB(pathlib.Path(d) / "t.db")
            oid, added = pipeline.add(db, CFG, "https://example.org/fellowship", org="Example Org",
                                      title="Example Fellowship", deadline="2030-01-15", infer=False)
            self.assertTrue(added and oid.startswith("m-"))
            r = db.get(oid)
            self.assertEqual((r["kind"], r["tier"]), ("fellowship", "solid"))
            self.assertEqual(pipeline.add(db, CFG, "https://example.org/fellowship", org="X", title="Y", infer=False)[1], False)
            db.close()


class Documents(unittest.TestCase):
    def test_resume_docx_is_valid(self):
        spec = json.loads((config.EXAMPLE / "resume.json").read_text())
        with tempfile.TemporaryDirectory() as d:
            path, pdf, _ = docs.resume(spec, {"name": "Alex Rivera", "email": "a@example.com",
                                              "links": [{"label": "site", "url": "https://example.com"}]}, d, pdf=False)
            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())
                xml = z.read("word/document.xml").decode()
                rels = z.read("word/_rels/document.xml.rels").decode()
            self.assertTrue({"[Content_Types].xml", "word/document.xml", "word/numbering.xml"} <= names)
            self.assertIn("ALEX RIVERA", xml)
            self.assertIn('Target="mailto:a@example.com"', rels)
            self.assertIsNone(pdf)

    def test_letters(self):
        items = json.loads((config.EXAMPLE / "letters.json").read_text())
        with tempfile.TemporaryDirectory() as d:
            (path, words), = docs.letters(items, {"name": "Alex Rivera"}, d, pdf=False, date="January 1, 2030")
            self.assertEqual(path.name, "Alex_Rivera_Cover_Letter_Example_Co.docx")
            self.assertGreater(words, 150)


class Server(TempDB):
    def setUp(self):
        super().setUp()
        from applyanything import server
        self.db.upsert([opp("a", "A")], NOW)
        self.httpd, self.token = server.make_server(self.db.path, CFG, 0)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        super().tearDown()

    def call(self, path, method="GET", body=None, headers=None):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read() or b"null") if "json" in r.headers.get("Content-Type", "") else r.read()
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"null")

    def test_page_embeds_token(self):
        code, page = self.call("/")
        self.assertEqual(code, 200)
        self.assertIn(self.token.encode(), page)

    def test_writes_need_token(self):
        self.assertEqual(self.call("/api/opportunities/a/application", "PATCH", {"status": "applied"})[0], 403)
        code, row = self.call("/api/opportunities/a/application", "PATCH", {"status": "applied"}, {"X-AA-Token": self.token})
        self.assertEqual((code, row["status"]), (200, "applied"))

    def test_rejects_foreign_host(self):
        self.assertEqual(self.call("/api/summary", headers={"Host": "attacker.example"})[0], 403)

    def test_validation(self):
        h = {"X-AA-Token": self.token}
        self.assertEqual(self.call("/api/opportunities/a/application", "PATCH", {"status": "bogus"}, h)[0], 400)
        self.assertEqual(self.call("/api/opportunities/a/application", "PATCH", {"effort": 1}, h)[0], 400)
        self.assertEqual(self.call("/api/opportunities", "POST", {"url": "javascript:alert(1)"}, h)[0], 400)
        self.assertEqual(self.call("/api/opportunities/missing")[0], 404)

    def test_listing_and_summary(self):
        code, d = self.call("/api/opportunities?q=software&status=open")
        self.assertEqual((code, d["total"]), (200, 1))
        self.assertEqual(self.call("/api/summary")[1]["counts"]["total"], 1)


if __name__ == "__main__":
    unittest.main()
