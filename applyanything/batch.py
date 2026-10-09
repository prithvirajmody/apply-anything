"""Group open opportunities into batches: one batch is one sitting with the agent.

Rounds come first. Applications tagged with a `round` number (the ones the agent
filled in one sitting) become one frozen batch per round. A batch is "started"
once any of its opportunities has a status other than "skipped"; started batches
are kept as they are. Every rebuild re-plans the unstarted batches from whatever
is still open, so new opportunities slot in by priority and closed ones drop out.

Left out (still visible in the UI): ineligible titles, anything flagged citizen /
no-sponsor / location / closed, inactive listings, and anything with a status.

Modes
  prestige  every reach opportunity first, then competitive, solid, accessible
  mixed     each batch mixes tiers by [batch] mix (default 2/3/3/2); an empty
            tier's slots go to the next tier down, then up
  deadline  soonest deadline first (hackathons, fellowships, grants); no deadline last

Within a tier, priority is: fit +40 (title matches [rank] fit and not far),
freshness up to +20 (posted today, falling to 0 at freshness_days), +5 when the
agent can fill it without an account. Titles far from your profile go last.
One opportunity per org across all batches (per_org); repeat postings of a
role already in play (same org and title) are dropped.
"""
import re
import time

from .db import SUBMITTED
from .rank import matches, words

BLOCKING = {"citizen", "no-sponsor", "location", "closed"}
ORDER = ["reach", "competitive", "solid", "accessible"]


def minutes(r):
    """Rough minutes of your time for one application, given who fills it."""
    m = {"agent": 4, "account": 12, "check": 10}.get(r.get("filler"), 10)
    essays = re.search(r"(\d+) written answer", r.get("note") or "")
    m += 5 * int(essays.group(1)) if essays else 0
    m += 8 if "cover letter" in (r.get("note") or "") else 0
    return m


def priority(r, now, fit, far, days):
    s = 0
    if matches(fit, r["title"]) and not matches(far, r["title"]):
        s += 40
    elif matches(far, r["title"]):
        s -= 30
    seen = r.get("posted_at") or r.get("first_seen") or now
    s += max(0, 20 * (1 - (now - seen) / (days * 86400)))
    s += 5 if r.get("filler") == "agent" else 0
    return s


def build(rows, cfg, old=None, mode=None, now=None):
    """Return (plan, summary). rows are joined opportunity + application dicts from DB.rows()."""
    now = now or time.time()
    bc = cfg["batch"]
    size, per_org, mode = bc["size"], bc["per_org"], mode or bc["mode"]
    mix = {g: bc["mix"].get(g, 0) for g in ORDER}
    fit, far = words(cfg["rank"]["fit"]), words(cfg["rank"]["far"])
    by_id = {r["id"]: r for r in rows}
    status = {r["id"]: r.get("status") or "" for r in rows}

    rounds = {}
    for r in rows:
        if r.get("round"):
            rounds.setdefault(r["round"], []).append(r["id"])
    in_round = {i for ids in rounds.values() for i in ids}
    round_batches = [{"ids": sorted(ids, key=lambda i: by_id[i]["org"]), "round": n} for n, ids in sorted(rounds.items())]
    kept = []
    for b in (old or {}).get("batches", []):
        ids = [i for i in b["ids"] if i not in in_round and i in by_id]
        if not b.get("round") and any(status.get(i) not in ("", "skipped") for i in ids):
            kept.append({"ids": ids})
    used = in_round | {i for b in kept for i in b["ids"]}

    pool = [r for r in rows if r["id"] not in used and not status[r["id"]] and r.get("active", 1)
            and r.get("tier") != "ineligible" and not BLOCKING & set(r.get("flags") or [])]
    pool.sort(key=lambda r: -priority(r, now, fit, far, bc["freshness_days"]))
    if mode == "deadline":
        pool.sort(key=lambda r: r.get("deadline") or float("inf"))

    # orgs you already went after count toward the per-org cap; repeat postings are dropped
    active = [r for r in rows if status[r["id"]] not in ("", "skipped")]
    taken = {(r["org"], r["title"]) for r in active}
    count = {}
    for r in active:
        count[r["org"]] = count.get(r["org"], 0) + 1
    for i in used:
        if status.get(i) in ("", "skipped"):
            count[by_id[i]["org"]] = count.get(by_id[i]["org"], 0) + 1
    tiers, extra, repeats = {g: [] for g in ORDER}, [], 0
    for r in pool:
        if (r["org"], r["title"]) in taken:
            continue
        taken.add((r["org"], r["title"]))
        count[r["org"]] = count.get(r["org"], 0) + 1
        if per_org and count[r["org"]] > per_org:
            repeats += 1
            continue
        ok = not matches(far, r["title"]) and r.get("tier") in tiers
        (tiers[r["tier"]] if ok else extra).append(r)

    if mode == "mixed":
        queue = []
        while any(tiers.values()):
            batch = []
            for g in ORDER:
                for _ in range(mix[g]):
                    k = ORDER.index(g)
                    # this tier, else the nearest tier below it, else above it
                    src = next((t for t in ORDER[k:] + ORDER[k - 1::-1] if tiers[t]), None)
                    if src and len(batch) < size:
                        batch.append(tiers[src].pop(0))
            if not batch:
                break
            queue += batch
    elif mode == "deadline":
        queue = sorted((r for g in ORDER for r in tiers[g]), key=lambda r: r.get("deadline") or float("inf"))
    else:
        queue = [r for g in ORDER for r in tiers[g]]
    queue += extra

    batches = [dict(b, mins=sum(minutes(by_id[i]) for i in b["ids"])) for b in round_batches + kept]
    for k in range(0, len(queue), size):
        chunk = queue[k:k + size]
        batches.append({"ids": [r["id"] for r in chunk], "mins": sum(minutes(r) for r in chunk)})
    for n, b in enumerate(batches, 1):
        b["n"] = n
    plan = {"generatedAt": int(now), "size": size, "mode": mode, "batches": batches}
    summary = {"rounds": len(round_batches), "kept": len(kept), "rebuilt": len(batches) - len(kept) - len(round_batches),
               "open": len(queue), "far": len(extra), "repeats": repeats}
    return plan, summary


def current(plan, rows):
    """The first batch that still has something not yet submitted or skipped."""
    status = {r["id"]: r.get("status") or "" for r in rows}
    for b in (plan or {}).get("batches", []):
        if any(status.get(i, "") in ("", "saved") for i in b["ids"]):
            return b
    return None


def progress(b, rows):
    status = {r["id"]: r.get("status") or "" for r in rows}
    done = sum(1 for i in b["ids"] if status.get(i) in SUBMITTED)
    skipped = sum(1 for i in b["ids"] if status.get(i) == "skipped")
    return {"done": done, "skipped": skipped, "total": len(b["ids"])}
