"""aa: the command line for Apply Anything. Run `./aa -h` or `./aa <command> -h`."""
import argparse
import csv
import datetime as dt
import json
import pathlib
import shutil
import sys
import time

from . import batch, config, docs, insights, pipeline
from .db import DB, LABELS, STATUSES


def fmt_date(ts):
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""


def table(rows, cols):
    """Print rows as a plain fixed-width table. cols = [(header, key or callable, max width)]."""
    cells = [[str(f(r) if callable(f) else (r.get(f) if r.get(f) is not None else ""))[:w] for _, f, w in cols] for r in rows]
    widths = [max([len(h)] + [len(c[i]) for c in cells]) for i, (h, _, _) in enumerate(cols)]
    print("  ".join(h.ljust(widths[i]) for i, (h, _, _) in enumerate(cols)).rstrip())
    for c in cells:
        print("  ".join(v.ljust(widths[i]) for i, v in enumerate(c)).rstrip())


ROW_COLS = [("id", "id", 46), ("org", "org", 24), ("title", "title", 44), ("kind", "kind", 11), ("tier", "tier", 11),
            ("effort", "effort", 6), ("fills", "filler", 7), ("status", "status", 10)]


def open_db():
    return DB(config.db_path())


def resolve(db, text):
    oid = db.find(text)
    if not oid:
        sys.exit(f"no single opportunity matches {text!r} (use a full id from `aa list`)")
    return oid


def out_json(obj):
    print(json.dumps(obj, indent=2, default=str, ensure_ascii=False))


# ---- commands --------------------------------------------------------------------
def cmd_init(a):
    home = config.home()
    home.mkdir(parents=True, exist_ok=True)
    made = []
    for src in sorted(config.EXAMPLE.rglob("*")):
        dst = home / src.relative_to(config.EXAMPLE)
        if src.is_dir():
            dst.mkdir(exist_ok=True)
        elif not dst.exists():
            shutil.copy2(src, dst)
            made.append(dst.relative_to(home))
    open_db().close()
    print(f"profile: {home}")
    for m in made:
        print(f"  created {m}")
    print("Next: fill in config.toml [identity] and packet.md, then `./aa sync` and `./aa ui`.")


def cmd_sync(a):
    db, cfg = open_db(), config.load()
    if not cfg["sources"]:
        sys.exit("no [[sources]] in config.toml; add one (see examples/profile/config.toml)")
    pipeline.sync(db, cfg, a.source, fetch_questions=False if a.no_questions else None)
    plan, s = pipeline.rebatch(db, cfg)
    print(f"batches: {len(plan['batches'])} ({s['rounds']} rounds, {s['kept']} started kept, {s['rebuilt']} rebuilt, "
          f"mode {plan['mode']})")


def cmd_rank(a):
    db, cfg = open_db(), config.load()
    pipeline.rerank(db, cfg, fetch_questions=False if a.no_questions else None)


def cmd_add(a):
    db, cfg = open_db(), config.load()
    oid, added = pipeline.add(db, cfg, a.url, org=a.org, title=a.title, kind=a.kind, deadline=a.deadline,
                              location=a.location, note=a.note, infer=not a.no_lookup)
    r = db.get(oid)
    print(f"{'added' if added else 'already tracked'}: {oid}  {r['org']}  {r['title']}  ({r['kind']}, {r['tier']}, "
          f"{r['platform'] or 'own portal'})")


def cmd_import(a):
    db, cfg = open_db(), config.load()
    path = pathlib.Path(a.file)
    items = json.loads(path.read_text()) if path.suffix == ".json" else list(csv.DictReader(path.open()))
    n = 0
    for it in items:
        if not it.get("url"):
            continue
        _, added = pipeline.add(db, cfg, it["url"], org=it.get("org") or None, title=it.get("title") or None,
                                kind=it.get("kind") or a.kind, deadline=it.get("deadline") or None,
                                location=it.get("location") or None, note=it.get("note") or None,
                                infer=not (it.get("org") and it.get("title")))
        n += added
    print(f"imported {n} new of {len(items)}")


def cmd_list(a):
    db = open_db()
    rows = db.rows()
    if a.batch:
        plan = db.kv("plan") or {"batches": []}
        b = next((b for b in plan["batches"] if b["n"] == a.batch), None)
        if not b:
            sys.exit(f"no batch {a.batch}")
        by_id = {r["id"]: r for r in rows}
        rows = [by_id[i] for i in b["ids"] if i in by_id]
    else:
        q = {k: [v] for k, v in {"status": a.status, "tier": a.tier, "kind": a.kind, "q": a.q,
                                 "sort": a.sort, "show": "all" if a.all else ""}.items() if v}
        from .server import filter_rows
        rows = filter_rows(rows, q)
    rows = rows[:a.limit] if a.limit else rows
    if a.json:
        return out_json(rows)
    table(rows, ROW_COLS + [("deadline", lambda r: fmt_date(r.get("deadline")), 10)])
    print(f"\n{len(rows)} shown")


def cmd_show(a):
    db = open_db()
    r = db.get(resolve(db, a.id))
    if a.json:
        return out_json(r)
    print(f"{r['org']} — {r['title']}\n{r['url']}\n")
    for k in ("id", "kind", "category", "tier", "effort", "platform", "filler", "note", "flags"):
        print(f"  {k:<10} {r.get(k)}")
    print(f"  {'locations':<10} {', '.join(r.get('locations') or [])}")
    print(f"  {'posted':<10} {fmt_date(r.get('posted_at'))}   deadline {fmt_date(r.get('deadline')) or '-'}"
          f"   listed {'yes' if r['active'] else 'no'}")
    print(f"\n  status     {r.get('status') or '-'} ({LABELS.get(r.get('status') or '', '')})")
    for k in ("round", "iteration", "variant", "referral", "notes"):
        if r.get(k) not in (None, "", {}):
            print(f"  {k:<10} {r[k]}")
    if r.get("applied_at"):
        print(f"  {'applied':<10} {fmt_date(r['applied_at'])}")
    for q, ans in (r.get("answers") or {}).items():
        print(f"  answer     {q} = {ans}")
    if r["events"]:
        print("\n  timeline")
        for e in r["events"]:
            print(f"    {fmt_date(e['at'])}  {e['status'] or '-':<10} {e['text']}")


def cmd_set(a):
    db = open_db()
    oid = resolve(db, a.id)
    f = {}
    if a.status is not None:
        if a.status and a.status not in STATUSES:
            sys.exit(f"status must be one of: {', '.join(STATUSES)} (or '' to clear)")
        f["status"] = a.status
    if a.note is not None:
        f["notes"] = a.note
    if a.add_note:
        old = (db.get(oid).get("notes") or "").strip()
        f["notes"] = (old + "\n" if old else "") + f"{fmt_date(time.time())}: {a.add_note}"
    for k in ("round", "iteration", "variant"):
        if getattr(a, k) is not None:
            f[k] = getattr(a, k)
    if a.answer:
        f["answers"] = dict(x.split("=", 1) for x in a.answer)
    if a.referral:
        f["referral"] = {"name": a.referral, "date": fmt_date(time.time())}
    if not f:
        sys.exit("nothing to set (see `aa set -h`)")
    d = db.set_app(oid, **f)
    print(f"{oid}: " + ", ".join(f"{k}={d.get(k)!r}" for k in f))


def cmd_event(a):
    db = open_db()
    oid = resolve(db, a.id)
    if a.status and a.status not in STATUSES:
        sys.exit(f"status must be one of: {', '.join(STATUSES)}")
    at = pipeline.parse_date(a.date) or int(time.time())
    added, status = db.add_event(oid, at, a.status or "", a.text or "", a.link, a.thread, a.msg, a.source)
    print(f"{oid}: " + (f"event added; status now {status or '-'}" if added else "already recorded (same message), skipped"))


def cmd_batch(a):
    db, cfg = open_db(), config.load()
    plan, s = pipeline.rebatch(db, cfg, a.mode, a.dry_run)
    rows = {r["id"]: r for r in db.rows()}
    print(f"{'preview' if a.dry_run else 'saved'}: {len(plan['batches'])} batches, mode {plan['mode']} "
          f"({s['rounds']} rounds, {s['kept']} started kept, {s['rebuilt']} rebuilt from {s['open']} open; "
          f"{s['far']} far from your profile queued last; {s['repeats']} org repeats left out)")
    cur = batch.current(plan, list(rows.values()))
    shown = [b for b in plan["batches"] if cur and b["n"] >= cur["n"]][:a.show]
    for b in shown:
        print(f"\nbatch {b['n']}" + (f" (round {b['round']})" if b.get("round") else "") + f", ~{b['mins']} min")
        for i in b["ids"]:
            r = rows[i]
            print(f"  {r['org'][:26]:<26} {r['title'][:52]:<52} {r.get('tier') or '':<11} {r.get('status') or ''}")


def cmd_next(a):
    db = open_db()
    rows = db.rows()
    b = batch.current(db.kv("plan"), rows)
    if not b:
        sys.exit("no open batch; run `aa sync` or `aa batch`")
    by_id = {r["id"]: r for r in rows}
    items = [by_id[i] for i in b["ids"] if i in by_id]
    if a.json:
        return out_json({**b, "rows": items})
    p = batch.progress(b, rows)
    print(f"batch {b['n']}" + (f" (round {b['round']})" if b.get("round") else "")
          + f": {p['done']}/{p['total']} submitted, {p['skipped']} skipped, ~{b['mins']} min\n")
    table(items, ROW_COLS)


def cmd_stats(a):
    db, cfg = open_db(), config.load()
    s = insights.summary(db, cfg)
    if a.json:
        return out_json({k: s[k] for k in ("counts", "funnel", "scoreboard", "sync", "plan")})
    c = s["counts"]
    print(f"{c['total']} tracked, {c['active']} listed now, {c['open']} open and eligible\n")
    print("funnel: " + "  ->  ".join(f"{f['label']} {f['n']}" for f in s["funnel"]))
    print("by status: " + ", ".join(f"{k or 'not started'} {v}" for k, v in c["byStatus"].items()))
    if s["scoreboard"]:
        print()
        table(s["scoreboard"], [("iteration", "iteration", 9), ("submitted", "submitted", 9),
                                ("rejected<=3d", "fastRejected", 12), ("rejected later", "laterRejected", 14),
                                ("assessment", "assessment", 10), ("(auto)", "autoAssessment", 6),
                                ("interview", "interview", 9), ("offer", "offer", 5), ("pending", "pending", 7)])
    for n, st in (s["sync"] or {}).items():
        print(f"\nsource {n}: last sync {fmt_date(st.get('at'))}, {st.get('count', '?')} open"
              + (f"; last error: {st['error']}" if st.get("error") else ""))


def cmd_ui(a):
    from . import server
    if a.demo:
        from . import demo
        path, cfg = demo.build()
        return server.serve(path, cfg, a.port if a.port is not None else 8766, not a.no_open, demo=True)
    cfg = config.load()
    open_db().close()
    server.serve(config.db_path(), cfg, a.port if a.port is not None else cfg["ui"]["port"], not a.no_open)


def cmd_resume(a):
    cfg = config.load()
    spec = json.loads(pathlib.Path(a.content).read_text())
    out = pathlib.Path(a.out or config.home() / "files")
    path, pdf, pages = docs.resume(spec, cfg["identity"], out, a.name, a.max_pages, not a.no_pdf)
    print(f"{pdf or path}" + (f" ({pages} page{'s' if pages != 1 else ''})" if pages else
                              "" if a.no_pdf else "  (no PDF: install LibreOffice for soffice)"))


def cmd_letters(a):
    cfg = config.load()
    items = json.loads(pathlib.Path(a.file).read_text())
    if a.key:
        items = [L for L in items if L["key"] in a.key]
    for path, words in docs.letters(items, cfg["identity"], pathlib.Path(a.out or config.home() / "files" / "letters"),
                                    not a.no_pdf):
        print(f"{path}  ({words} words)")


def cmd_export(a):
    db = open_db()
    rows = db.rows()
    dst = open(a.out, "w", newline="") if a.out else sys.stdout
    if a.format == "csv":
        w = csv.writer(dst)
        cols = ["id", "org", "title", "kind", "status", "tier", "effort", "platform", "url", "deadline", "applied_at", "notes"]
        w.writerow(cols)
        for r in rows:
            w.writerow([fmt_date(r.get(c)) if c in ("deadline", "applied_at") else r.get(c) or "" for c in cols])
    else:
        json.dump({"opportunities": rows, "events": db.events(), "plan": db.kv("plan")}, dst, indent=1, default=str)
    if a.out:
        dst.close()
        print(f"wrote {a.out}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="aa", description="Apply Anything: find, rank, fill and track applications.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create your profile folder from examples/profile").set_defaults(fn=cmd_init)
    s = sub.add_parser("sync", help="pull every configured source, re-rank, rebuild batches")
    s.add_argument("--source", help="only this source (name or type)")
    s.add_argument("--no-questions", action="store_true", help="don't read Greenhouse forms for essay counts")
    s.set_defaults(fn=cmd_sync)
    s = sub.add_parser("rank", help="re-score everything with the current config")
    s.add_argument("--no-questions", action="store_true")
    s.set_defaults(fn=cmd_rank)

    s = sub.add_parser("add", help="track any opportunity by URL (job, hackathon, fellowship, grant, event...)")
    s.add_argument("url")
    s.add_argument("--org")
    s.add_argument("--title")
    s.add_argument("--kind", help="job, internship, hackathon, fellowship, scholarship, grant, program, event, other")
    s.add_argument("--deadline", help="YYYY-MM-DD")
    s.add_argument("--location")
    s.add_argument("--note")
    s.add_argument("--no-lookup", action="store_true", help="don't fetch the page to fill in org and title")
    s.set_defaults(fn=cmd_add)
    s = sub.add_parser("import", help="add many from a CSV or JSON file (url, org, title, kind, deadline, location, note)")
    s.add_argument("file")
    s.add_argument("--kind")
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser("list", help="list opportunities")
    s.add_argument("--status", help="comma list; 'open' = not started")
    s.add_argument("--tier")
    s.add_argument("--kind")
    s.add_argument("--q", help="search org, title, location, notes")
    s.add_argument("--batch", type=int)
    s.add_argument("--sort", choices=["effort", "-effort", "newest", "deadline", "org", "updated"])
    s.add_argument("--all", action="store_true", help="include ones no longer listed")
    s.add_argument("--limit", type=int, default=0)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_list)
    s = sub.add_parser("show", help="one opportunity with its application and timeline")
    s.add_argument("id", help="id, unique id prefix, or org name")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_show)

    s = sub.add_parser("set", help="update your application (status, notes, answers given, resume variant...)")
    s.add_argument("id")
    s.add_argument("--status", help=", ".join(STATUSES))
    s.add_argument("--note", help="replace the notes")
    s.add_argument("--add-note", help="append a dated line to the notes")
    s.add_argument("--round", type=int, help="the sitting this was filled in (freezes it as a batch)")
    s.add_argument("--iteration", type=int, help="iteration number from your iteration log")
    s.add_argument("--variant", help="resume variant sent")
    s.add_argument("--answer", action="append", metavar="QUESTION=ANSWER", help="a knockout answer given (repeatable)")
    s.add_argument("--referral", metavar="NAME")
    s.set_defaults(fn=cmd_set)
    s = sub.add_parser("event", help="add a timeline event (moves the status forward if it's a later step)")
    s.add_argument("id")
    s.add_argument("--status", default="", help=", ".join(STATUSES))
    s.add_argument("--text", default="")
    s.add_argument("--date", help="YYYY-MM-DD (default now)")
    s.add_argument("--link")
    s.add_argument("--thread", help="email thread id")
    s.add_argument("--msg", help="email message id (dedupes re-scans)")
    s.add_argument("--source", default="manual", help="manual, email, agent")
    s.set_defaults(fn=cmd_event)

    s = sub.add_parser("batch", help="rebuild the unstarted batches")
    s.add_argument("--mode", choices=["prestige", "mixed", "deadline"])
    s.add_argument("--dry-run", action="store_true", help="preview without saving")
    s.add_argument("--show", type=int, default=1, help="how many upcoming batches to print")
    s.set_defaults(fn=cmd_batch)
    s = sub.add_parser("next", help="the current batch")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_next)
    s = sub.add_parser("stats", help="funnel and per-iteration scoreboard")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_stats)

    s = sub.add_parser("ui", help="open the web UI")
    s.add_argument("--port", type=int, help="default 8765 (8766 for --demo); 0 picks a free port")
    s.add_argument("--no-open", action="store_true", help="don't open a browser tab")
    s.add_argument("--demo", action="store_true", help="fictional sample data, nothing from your profile")
    s.set_defaults(fn=cmd_ui)

    s = sub.add_parser("resume", help="build a one-page resume (.docx + .pdf) from JSON")
    s.add_argument("content")
    s.add_argument("--out")
    s.add_argument("--name", help="file name without extension")
    s.add_argument("--max-pages", type=int, default=1)
    s.add_argument("--no-pdf", action="store_true")
    s.set_defaults(fn=cmd_resume)
    s = sub.add_parser("letters", help="build cover letters (.docx + .pdf) from JSON")
    s.add_argument("file")
    s.add_argument("--key", action="append", help="only these letter keys")
    s.add_argument("--out")
    s.add_argument("--no-pdf", action="store_true")
    s.set_defaults(fn=cmd_letters)
    s = sub.add_parser("export", help="dump everything as JSON or CSV")
    s.add_argument("--format", choices=["json", "csv"], default="json")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_export)

    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
