"""Numbers for the dashboard, `aa stats` and /retro: the funnel and a per-iteration scoreboard."""
import time

from . import batch
from .db import LEVEL, SUBMITTED

FAST_DAYS = 3        # a rejection this soon after applying almost always comes from an automated knockout
AUTO_SECONDS = 3600  # an assessment invite this soon after applying is sent to everyone


def mini(r):
    keys = ("id", "org", "title", "kind", "tier", "filler", "platform", "status", "deadline", "url", "effort", "flags")
    return {k: r.get(k) for k in keys}


def by_opp(events):
    out = {}
    for e in events:
        out.setdefault(e["opp_id"], []).append(e)
    for evs in out.values():
        evs.sort(key=lambda e: e["at"])
    return out


def reached(r, evs):
    """Furthest pipeline step an application got to (a rejection after an interview still reached interview)."""
    return max([LEVEL.get(r.get("status") or "", 0)] + [LEVEL.get(e["status"], 0) for e in evs])


def scoreboard(rows, events):
    ev = by_opp(events)
    out = {}
    for r in rows:
        if r.get("status") not in SUBMITTED:
            continue
        it = r.get("iteration") or 0
        s = out.setdefault(it, {"iteration": it, "submitted": 0, "fastRejected": 0, "laterRejected": 0,
                                "assessment": 0, "autoAssessment": 0, "interview": 0, "offer": 0, "pending": 0})
        evs = ev.get(r["id"], [])
        lv = reached(r, evs)
        s["submitted"] += 1
        s["assessment"] += lv >= LEVEL["assessment"]
        s["interview"] += lv >= LEVEL["interview"]
        s["offer"] += lv >= LEVEL["offer"]
        first_oa = next((e for e in evs if e["status"] == "assessment"), None)
        if first_oa and r.get("applied_at") and first_oa["at"] - r["applied_at"] <= AUTO_SECONDS:
            s["autoAssessment"] += 1
        if r["status"] == "rejected":
            rej = next((e for e in reversed(evs) if e["status"] == "rejected"), None)
            fast = rej and r.get("applied_at") and (rej["at"] - r["applied_at"]) <= FAST_DAYS * 86400
            s["fastRejected" if fast else "laterRejected"] += 1
        if r["status"] == "applied":
            s["pending"] += 1
    return [out[k] for k in sorted(out)]


def summary(db, cfg, now=None):
    now = now or time.time()
    rows = db.rows()
    events = db.events()
    plan = db.kv("plan")
    count = lambda key: {k: sum(1 for r in rows if (r.get(key) or "") == k) for k in sorted({r.get(key) or "" for r in rows})}
    submitted = [r for r in rows if r.get("status") in SUBMITTED]
    ev = by_opp(events)
    lv = {r["id"]: reached(r, ev.get(r["id"], [])) for r in submitted}
    nxt = batch.current(plan, rows)
    by_id = {r["id"]: r for r in rows}
    open_rows = [r for r in rows if not r.get("status") and r.get("active") and r.get("tier") != "ineligible"
                 and not batch.BLOCKING & set(r.get("flags") or [])]
    deadlines = sorted((r for r in rows if r.get("deadline") and now <= r["deadline"] <= now + 21 * 86400
                        and (r.get("status") or "") in ("", "saved") and r.get("active")),
                       key=lambda r: r["deadline"])
    return {
        "identity": {"name": cfg["identity"].get("name", "")},
        "counts": {"total": len(rows), "active": sum(1 for r in rows if r.get("active")), "open": len(open_rows),
                   "byStatus": count("status"), "byKind": count("kind"), "byTier": count("tier")},
        "funnel": [
            {"key": "applied", "label": "Submitted", "n": len(submitted)},
            {"key": "assessment", "label": "Assessment", "n": sum(1 for v in lv.values() if v >= LEVEL["assessment"])},
            {"key": "interview", "label": "Interview", "n": sum(1 for v in lv.values() if v >= LEVEL["interview"])},
            {"key": "offer", "label": "Offer / accepted", "n": sum(1 for v in lv.values() if v >= LEVEL["offer"])},
        ],
        "sync": db.kv("sync", {}),
        "plan": {"mode": (plan or {}).get("mode"), "generatedAt": (plan or {}).get("generatedAt"),
                 "batches": len((plan or {}).get("batches", []))},
        "next": nxt and {**nxt, "progress": batch.progress(nxt, rows), "rows": [mini(by_id[i]) for i in nxt["ids"] if i in by_id]},
        "saved": [mini(r) for r in rows if r.get("status") == "saved"],
        "deadlines": [mini(r) for r in deadlines[:12]],
        "recent": events[:15],
        "scoreboard": scoreboard(rows, events),
        "sources": [{"name": s.get("name") or s["type"], "type": s["type"]} for s in cfg["sources"]],
        "weekly": weekly(submitted, now),
        "openByTier": [{"tier": g, "n": sum(1 for r in open_rows if r.get("tier") == g)} for g in batch.ORDER],
    }


def weekly(submitted, now, weeks=12):
    """Applications submitted per week (Monday start) for the last `weeks` weeks, oldest first."""
    today = time.localtime(now)
    start = time.mktime((today.tm_year, today.tm_mon, today.tm_mday - today.tm_wday, 0, 0, 0, 0, 0, -1))
    starts = [start - 7 * 86400 * k for k in range(weeks - 1, -1, -1)]
    out = [{"week": int(w), "n": 0} for w in starts]
    for r in submitted:
        at = r.get("applied_at")
        if not at or at < starts[0]:
            continue
        k = min(int((at - starts[0]) // (7 * 86400)), weeks - 1)
        out[k]["n"] += 1
    return out
