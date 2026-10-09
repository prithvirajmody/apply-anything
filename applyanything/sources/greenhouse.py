"""Every open posting on one or more Greenhouse job boards.

[[sources]]
type = "greenhouse"
boards = ["stripe", "figma"]     # the board token: job-boards.greenhouse.io/<token>
include = ["intern"]             # title regexes; empty = everything
exclude = ["phd"]
kind = "internship"
"""
import datetime as dt

from . import get_json, title_filter


def ts(s):
    return int(dt.datetime.fromisoformat(s).timestamp()) if s else None


def fetch(src):
    keep = title_filter(src)
    rows = []
    for board in src.get("boards", []):
        d = get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs")
        for j in d.get("jobs", []):
            if not keep(j["title"]):
                continue
            loc = (j.get("location") or {}).get("name") or ""
            rows.append({
                "id": f"gh-{board}-{j['id']}", "org": j.get("company_name") or board, "title": j["title"].strip(),
                "kind": src.get("kind", "job"), "category": src.get("category", ""),
                "locations": [l.strip() for l in loc.split(";") if l.strip()] if loc else [],
                "url": j["absolute_url"], "posted_at": ts(j.get("first_published") or j.get("updated_at")),
                "deadline": ts(j.get("application_deadline")), "extra": {"gh_board": board},
            })
    return rows
