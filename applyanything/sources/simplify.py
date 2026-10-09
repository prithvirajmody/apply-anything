"""SimplifyJobs listings (the GitHub repos behind the community internship and new-grad lists).

[[sources]]
type = "simplify"
repo = "SimplifyJobs/Summer2027-Internships"   # or "SimplifyJobs/New-Grad-Positions"
branch = "dev"
kind = "internship"                            # "job" for new-grad roles
terms = ["Summer 2027"]                        # empty = any term
categories = { "Software" = "SWE", "AI/ML/Data" = "AI/ML" }   # empty = all
days = 30                                      # only postings from the last N days
degree = "Bachelor's"                          # drop postings that list degrees but not this one
stale_term = { term = "Summer 2026", posted_after = "2026-08-01" }   # optional
pinned = ["<listing id>"]                      # keep these whatever their age or term tag

stale_term: Simplify often tags a new season's postings with last season's term.
A posting with that term, posted after the date, counts as current.
"""
import datetime as dt
import time

from . import get_json


def fetch(src):
    url = f"https://raw.githubusercontent.com/{src['repo']}/{src.get('branch', 'dev')}/.github/scripts/listings.json"
    data = get_json(url, timeout=60)
    cats = src.get("categories") or {}
    terms = set(src.get("terms") or [])
    pinned = set(src.get("pinned") or [])
    cutoff = time.time() - src.get("days", 30) * 86400
    stale = src.get("stale_term")
    stale_after = dt.datetime.fromisoformat(stale["posted_after"]).timestamp() if stale else None
    degree = src.get("degree")
    rows = []
    for x in data:
        posted = x.get("date_posted", 0)
        xterms = x.get("terms") or []
        in_term = (not terms or terms & set(xterms)
                   or (stale and stale["term"] in xterms and posted >= stale_after))
        degrees = x.get("degrees") or []
        if not (x.get("active") and x.get("is_visible")):
            continue
        if x["id"] not in pinned and not (in_term and posted >= cutoff):
            continue
        if cats and x.get("category") not in cats:
            continue
        if degree and degrees and degree not in degrees:
            continue
        rows.append({
            "id": f"simplify-{x['id']}", "org": x["company_name"], "title": x["title"],
            "kind": src.get("kind", "internship"), "category": cats.get(x.get("category"), x.get("category") or ""),
            "locations": x.get("locations") or [], "url": x["url"], "posted_at": posted, "deadline": None,
            "extra": {"terms": xterms, "sponsorship": x.get("sponsorship")},
        })
    return rows
