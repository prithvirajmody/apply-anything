"""Every open posting for one or more companies on Lever.

[[sources]]
type = "lever"
companies = ["palantir"]         # jobs.lever.co/<company>
include = ["intern"]
kind = "internship"
"""
from . import get_json, title_filter


def fetch(src):
    keep = title_filter(src)
    rows = []
    for co in src.get("companies", []):
        for j in get_json(f"https://api.lever.co/v0/postings/{co}?mode=json"):
            if not keep(j["text"]):
                continue
            cat = j.get("categories") or {}
            locs = cat.get("allLocations") or ([cat["location"]] if cat.get("location") else [])
            rows.append({
                "id": f"lever-{co}-{j['id']}", "org": src.get("org_names", {}).get(co, co.replace("-", " ").title()),
                "title": j["text"].strip(), "kind": src.get("kind", "job"), "category": cat.get("team", ""),
                "locations": locs, "url": j.get("hostedUrl") or j.get("applyUrl"),
                "posted_at": int(j["createdAt"] / 1000) if j.get("createdAt") else None, "deadline": None,
                "extra": {"commitment": cat.get("commitment"), "workplace": j.get("workplaceType")},
            })
    return rows
