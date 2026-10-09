"""The steps the CLI and the UI share: sync sources, rank, rebuild batches, add by URL."""
import datetime as dt
import hashlib
import html
import re
import time
import urllib.parse
import urllib.request

from . import batch, rank, sources
from .sources import UA, get_json

KIND_HINTS = [
    ("hackathon", r"hackathon|hacks?\b|devpost|buildathon|game jam"),
    ("fellowship", r"fellowship|fellows?\b"),
    ("scholarship", r"scholarship"),
    ("grant", r"\bgrant\b|microgrant"),
    ("program", r"accelerator|incubator|residency|bootcamp|summer school|program\b|cohort"),
    ("event", r"conference|summit|meetup|lu\.ma|luma\.com|partiful|eventbrite"),
    ("internship", r"intern(ship)?\b|co-?op\b"),
]


def guess_kind(title, url=""):
    text = f"{title} {url}".lower()
    return next((k for k, rx in KIND_HINTS if re.search(rx, text)), "job")


def parse_date(s):
    """'2026-11-01' (end of that day, local time) or unix seconds -> unix seconds."""
    if s in (None, ""):
        return None
    if isinstance(s, (int, float)) or str(s).isdigit():
        return int(s)
    d = dt.datetime.fromisoformat(str(s))
    if len(str(s)) <= 10:
        d += dt.timedelta(hours=23, minutes=59)
    return int(d.timestamp())


def sync(db, cfg, only=None, log=print, fetch_questions=None):
    """Pull every configured source (or just `only`), store the results, then re-rank."""
    now = int(time.time())
    state = db.kv("sync", {})
    new = []
    for src in cfg["sources"]:
        n = sources.name(src)
        if only and only not in (n, src["type"]):
            continue
        try:
            rows = sources.fetch(src)
        except Exception as e:  # one broken feed shouldn't stop the others
            log(f"{n}: failed ({e})")
            state[n] = {**state.get(n, {}), "error": str(e), "errorAt": now}
            continue
        for r in rows:
            r["source"] = n
        added, _ = db.upsert(rows, now)
        gone = db.deactivate_missing(n, {r["id"] for r in rows})
        state[n] = {"at": now, "count": len(rows), "added": len(added), "closed": len(gone)}
        log(f"{n}: {len(rows)} open ({len(added)} new, {len(gone)} no longer listed)")
        fresh = set(added)
        new += [r for r in rows if r["id"] in fresh]
    db.set_kv("sync", state)
    rerank(db, cfg, log, fetch_questions)
    known = {o for g in ("reach", "competitive", "accessible") for o in cfg["rank"][g]}
    known |= set(cfg["eligibility"]["requires_citizenship"]) | set(cfg["eligibility"]["no_sponsorship"])
    unknown = sorted({r["org"] for r in new if r["org"] not in known})
    if unknown:
        log(f"{len(unknown)} new orgs aren't in any tier list (they count as 'solid'): "
            + ", ".join(unknown[:40]) + (" ..." if len(unknown) > 40 else ""))
    return {"sources": state, "new": len(new), "unknownOrgs": unknown}


def rerank(db, cfg, log=print, fetch_questions=None):
    rows = db.rows()
    before = sum(1 for r in rows if "gh_form" in (r.get("extra") or {}))
    rank.rank(rows, cfg, fetch_questions)
    db.save_rank(rows)
    fetched = sum(1 for r in rows if "gh_form" in (r.get("extra") or {})) - before
    log(f"ranked {len(rows)}" + (f" (read {fetched} Greenhouse forms)" if fetched else ""))
    return rows


def rebatch(db, cfg, mode=None, dry_run=False):
    plan, summary = batch.build(db.rows(), cfg, db.kv("plan"), mode)
    if not dry_run:
        db.set_kv("plan", plan)
    return plan, summary


# ---- adding any URL by hand -------------------------------------------------
def _page_meta(url):
    req = urllib.request.Request(url, headers={**UA, "Accept": "text/html"})
    raw = urllib.request.urlopen(req, timeout=15).read(400_000).decode("utf-8", "replace")
    def meta(prop):
        m = re.search(rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]+content=["\']([^"\']+)', raw, re.I)
        return html.unescape(m.group(1)).strip() if m else ""
    t = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    return {"title": meta("og:title") or (html.unescape(t.group(1)).strip() if t else ""), "site": meta("og:site_name")}


def lookup(url):
    """Best-effort org, title, location and stable id for a posting URL."""
    u = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(u.query)
    m = re.search(r"greenhouse\.io/([\w-]+)/jobs/(\d+)", url)
    board, job = (m.group(1), m.group(2)) if m else ((qs.get("for") or [None])[0], (qs.get("token") or [None])[0])
    try:
        if board and job and "greenhouse" in u.netloc:
            d = get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job}")
            loc = (d.get("location") or {}).get("name")
            return {"id": f"gh-{board}-{job}", "org": d.get("company_name") or board, "title": d["title"],
                    "locations": [loc] if loc else [], "extra": {"gh_board": board}}
        m = re.search(r"jobs\.lever\.co/([\w-]+)/([\w-]{36})", url)
        if m:
            d = get_json(f"https://api.lever.co/v0/postings/{m.group(1)}/{m.group(2)}")
            loc = (d.get("categories") or {}).get("location")
            return {"id": f"lever-{m.group(1)}-{m.group(2)}", "org": m.group(1).replace("-", " ").title(),
                    "title": d["text"], "locations": [loc] if loc else []}
        m = re.search(r"jobs\.ashbyhq\.com/([\w.-]+)/([\w-]{36})", url)
        if m:
            d = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{m.group(1)}")
            j = next((j for j in d.get("jobs", []) if j["id"] == m.group(2)), None)
            if j:
                return {"id": f"ashby-{m.group(1)}-{j['id']}", "org": m.group(1).replace("-", " ").title(),
                        "title": j["title"].strip(), "locations": [j["location"]] if j.get("location") else []}
        meta = _page_meta(url)
    except Exception:
        meta = {"title": "", "site": ""}
    host = u.netloc.lower().removeprefix("www.")
    org = meta["site"] or (host.split(".")[-2].replace("-", " ").title() if host.count(".") else host)
    return {"org": org, "title": meta["title"] or host}


def add(db, cfg, url, org=None, title=None, kind=None, deadline=None, location=None, note=None, infer=True):
    """Add any opportunity by URL. Returns (id, added?)."""
    info = lookup(url) if infer and not (org and title) else {}
    title = title or info.get("title") or url
    row = {
        "id": info.get("id") or "m-" + hashlib.sha1(url.encode()).hexdigest()[:10],
        "source": "manual", "org": org or info.get("org") or "Unknown", "title": title,
        "kind": kind or guess_kind(title, url), "category": "",
        "locations": [location] if location else info.get("locations", []),
        "url": url, "posted_at": int(time.time()), "deadline": parse_date(deadline),
        "extra": info.get("extra") or {},
    }
    if db.get(row["id"]):
        return row["id"], False
    db.upsert([row])
    if note:
        db.set_app(row["id"], notes=note)
    rows = db.rows()
    one = [r for r in rows if r["id"] == row["id"]]
    rank.rank(one, cfg)
    db.save_rank(one)
    return row["id"], True
