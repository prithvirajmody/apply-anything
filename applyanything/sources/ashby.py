"""Every listed posting for one or more organizations on Ashby.

[[sources]]
type = "ashby"
orgs = ["ramp"]                  # jobs.ashbyhq.com/<org>
include = ["intern"]
kind = "internship"
"""
import datetime as dt

from . import get_json, title_filter


def fetch(src):
    keep = title_filter(src)
    rows = []
    for org in src.get("orgs", []):
        d = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{org}")
        for j in d.get("jobs", []):
            title = j["title"].strip()
            if not j.get("isListed", True) or not keep(title):
                continue
            locs = [j["location"]] + [s["location"] for s in j.get("secondaryLocations") or []]
            pub = j.get("publishedAt")
            rows.append({
                "id": f"ashby-{org}-{j['id']}", "org": src.get("org_names", {}).get(org, org.replace("-", " ").title()),
                "title": title, "kind": src.get("kind", "job"), "category": j.get("department") or "",
                "locations": [l for l in locs if l], "url": j.get("jobUrl") or j.get("applyUrl"),
                "posted_at": int(dt.datetime.fromisoformat(pub).timestamp()) if pub else None, "deadline": None,
                "extra": {"employment": j.get("employmentType"), "remote": j.get("isRemote")},
            })
    return rows
