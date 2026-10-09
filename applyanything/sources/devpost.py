"""Open and upcoming hackathons listed on Devpost.

[[sources]]
type = "devpost"
online_only = false
themes = ["Machine Learning/AI"]   # keep hackathons with any of these themes; empty = all
include = []                       # title regexes
exclude = []
max_pages = 20                     # 9 hackathons per page
"""
import concurrent.futures as cf
import datetime as dt
import html
import re

from . import get_json, title_filter

API = "https://devpost.com/api/hackathons?status[]=upcoming&status[]=open&page={}"


def end_date(s):
    """'Aug 31 - Oct 23, 2026' / 'Oct 01 - 10, 2026' / 'Aug 23, 2026 - Jan 02, 2027' -> unix end of that day."""
    if not s:
        return None
    start, _, end = s.rpartition(" - ")
    end = end.strip()
    if not re.match(r"[A-Za-z]{3}", end):
        end = start.split()[0] + " " + end
    try:
        d = dt.datetime.strptime(end, "%b %d, %Y")
    except ValueError:
        return None
    return int((d + dt.timedelta(hours=23, minutes=59)).timestamp())


def fetch(src):
    keep = title_filter(src)
    themes = set(src.get("themes") or [])
    pages = range(1, src.get("max_pages", 20) + 1)
    with cf.ThreadPoolExecutor(6) as ex:
        results = list(ex.map(lambda p: get_json(API.format(p)).get("hackathons", []), pages))
    rows, seen = [], set()
    for h in (h for page in results for h in page):
        if h["id"] in seen:
            continue
        seen.add(h["id"])
        place = (h.get("displayed_location") or {}).get("location") or ""
        online = place.lower() == "online"
        names = {t["name"] for t in h.get("themes") or []}
        if (src.get("online_only") and not online) or (themes and not themes & names) or not keep(h["title"]):
            continue
        if h.get("invite_only"):
            continue
        prize = html.unescape(re.sub(r"<[^>]+>", "", h.get("prize_amount") or "")).strip()
        rows.append({
            "id": f"devpost-{h['id']}", "org": h.get("organization_name") or "Devpost", "title": h["title"].strip(),
            "kind": "hackathon", "category": ", ".join(sorted(names)), "locations": [place] if place else [],
            "url": h["url"], "posted_at": None, "deadline": end_date(h.get("submission_period_dates")),
            "extra": {"dates": h.get("submission_period_dates"), "prize": prize, "online": online,
                      "registrations": h.get("registrations_count"), "state": h.get("open_state")},
        })
    return rows
