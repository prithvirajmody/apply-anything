"""Score each opportunity by how much work it will take and how long the odds are,
flag the ones you probably can't apply to, and say who fills the form.

Writes these fields on every opportunity:
  effort    0-100; higher means more work and lower odds (the UI can sort by it)
  tier      reach | competitive | solid | accessible | ineligible
  filler    agent | account | check (see platforms.py)
  platform  Greenhouse, Workday, Luma, ...
  note      what the application needs from you, in a few words
  flags     citizen | no-sponsor | location | closed: reasons to keep it out of batches

Tiers come from the org lists in config.toml [rank]. They are judgment calls about
how selective each program is; anything unlisted counts as "solid".
"""
import concurrent.futures as cf
import json
import re
import time
import urllib.request

from . import platforms

US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY "
                "NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR".split())
US_NAMES = {"nyc", "sf", "la", "south sf", "remote in usa", "united states", "usa", "us", "remote", "remote (us)",
            "remote - us", "us remote", "online", "virtual", "anywhere"}
# Companies whose Greenhouse board sits behind their own careers page (?gh_jid= links)
GH_BOARDS = {"Waymo": "waymo", "Hudson River Trading": "wehrtyou", "Epic Games": "epicgames",
             "Tower Research Capital": "towerresearchcapital", "Lyft": "lyft", "Datadog": "datadog",
             "Stripe": "stripe"}
# Greenhouse form fields every application has; anything else that's required is a written answer or a knockout
STD_Q = {"First Name", "Last Name", "Email", "Phone", "Resume/CV", "Cover Letter", "LinkedIn Profile",
         "Preferred First Name", "Country", "Location (City)", "Website"}


def words(patterns):
    """Compile a list of phrases (each may be a regex) into one case-insensitive word-boundary pattern."""
    pats = [p for p in patterns if p]
    return re.compile(r"\b(?:" + "|".join(pats) + r")\b", re.I) if pats else None


def matches(rx, text):
    return bool(rx and text and rx.search(text))


def in_countries(locs, countries):
    """True if any location is in an allowed country. No locations, or no country filter, counts as allowed."""
    if not countries or not locs:
        return True
    want = [c.lower() for c in countries]
    for loc in locs:
        low = loc.strip().lower()
        if "us" in want or "usa" in want or "united states" in want:
            m = re.search(r",\s*([A-Z]{2})$", loc.strip())
            if low in US_NAMES or (m and m.group(1) in US_STATES) or "united states" in low or low.endswith(", usa"):
                return True
        if any(c in low for c in want if len(c) > 2):
            return True
    return False


def gh_target(r, boards=GH_BOARDS):
    m = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([\w-]+)/jobs/(\d+)", r["url"])
    if m:
        return m.group(1), m.group(2)
    board = (r.get("extra") or {}).get("gh_board") or boards.get(r["org"])
    m = re.search(r"gh_jid=(\d+)", r["url"])
    if m and board:
        return board, m.group(1)
    return None


def gh_questions(rows, timeout=30):
    """Fetch each Greenhouse form once: number of required essays, whether a cover letter is required,
    and the board's own title (aggregators sometimes relabel a role)."""
    def one(r):
        board, job = gh_target(r)
        try:
            d = json.load(urllib.request.urlopen(
                f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job}?questions=true", timeout=timeout))
        except Exception:
            return r["id"], None
        qs = d.get("questions", [])
        req = [q for q in qs if q["label"] not in STD_Q and q.get("required")]
        essays = sum(1 for q in req if any(f["type"] == "textarea" for f in q["fields"]))
        cover = any(q["label"] == "Cover Letter" and q.get("required") for q in qs)
        return r["id"], {"essays": essays, "cover": cover, "title": d.get("title", ""), "at": int(time.time())}

    todo = [r for r in rows if gh_target(r) and "gh_form" not in (r.get("extra") or {})]
    with cf.ThreadPoolExecutor(12) as ex:
        return {i: v for i, v in ex.map(one, todo) if v}


def tier(org, cfg):
    for g in ("reach", "competitive", "accessible"):
        if org in set(cfg["rank"][g]):
            return g
    return "solid"


def rank(rows, cfg, fetch_questions=None, now=None):
    """Score rows in place (each row is an opportunity dict) and return them."""
    now = now or time.time()
    rk, el = cfg["rank"], cfg["eligibility"]
    fit, far, inel = words(rk["fit"]), words(rk["far"]), words(rk["ineligible"])
    citizen, no_sponsor = set(el["requires_citizenship"]), set(el["no_sponsorship"])
    fetch = rk.get("questions", True) if fetch_questions is None else fetch_questions
    if fetch:
        by_id = {r["id"]: r for r in rows}
        for i, form in gh_questions([r for r in rows if r.get("active", 1)]).items():
            by_id[i]["extra"] = {**(by_id[i].get("extra") or {}), "gh_form": form}

    for r in rows:
        title, org = r["title"], r["org"]
        notes, flags = [], []
        g = tier(org, cfg)
        e = rk["base"].get(g, 42)
        if matches(fit, title) and not matches(far, title):
            e -= 8
        elif matches(far, title):
            e += 10
            notes.append("far from your profile; needs a tailored version")
        if org in citizen:
            flags.append("citizen")
            notes.append("usually requires citizenship or a security clearance")
        if el["needs_sponsorship"] and org in no_sponsor:
            flags.append("no-sponsor")
            notes.append("their postings say they don't sponsor visas")
        if r.get("kind") in el["location_kinds"] and not in_countries(r.get("locations") or [], el["countries"]):
            flags.append("location")
            notes.append("no location in the countries you can work in")
        if r.get("deadline") and r["deadline"] < now:
            flags.append("closed")
            notes.append("deadline has passed")

        platform, filler, how = platforms.detect(r["url"])
        notes.insert(0, how)
        if filler == "account":
            e += 4
        form = (r.get("extra") or {}).get("gh_form") or {}
        if form.get("essays"):
            n = form["essays"]
            e += 4 * n
            notes.append(f"{n} written answer{'s' if n > 1 else ''} (the agent drafts them)")
        if form.get("cover"):
            e += 8
            notes.append("cover letter required (the agent drafts it)")
        if matches(inel, title) or matches(inel, form.get("title", "")):
            g, e = "ineligible", 0
            notes.insert(0, "title targets a different year or degree; probably not eligible")

        r.update(effort=max(0, min(100, e)), tier=g, filler=filler, platform=platform,
                 note="; ".join(notes), flags=flags)
    return rows
