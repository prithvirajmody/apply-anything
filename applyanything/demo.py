"""A fictional dataset for `aa ui --demo`: made-up organizations, example.com links,
and a season's worth of statuses and email events. Nothing here comes from a profile."""
import pathlib
import random
import tempfile
import time

from . import batch, config, rank
from .db import DB

DAY = 86400
# (org, tier, title, kind, platform hint in the URL, locations)
OPPS = [
    ("Northwind Labs", "reach", "Software Engineer Intern, Summer 2027", "internship", "greenhouse", ["New York, NY"]),
    ("Kestrel Quant", "reach", "Quantitative Developer Intern", "internship", "myworkdayjobs", ["Chicago, IL"]),
    ("Parallax AI", "reach", "Machine Learning Engineer Intern", "internship", "ashbyhq", ["San Francisco, CA"]),
    ("Orbital Works", "reach", "Flight Software Intern", "internship", "lever.co", ["Seattle, WA"]),
    ("Vantage Research", "reach", "Research Engineer Intern, LLM Evaluation", "internship", "greenhouse", ["Remote"]),
    ("Tidewater Systems", "competitive", "Backend Engineer Intern", "internship", "greenhouse", ["Austin, TX"]),
    ("Juniper Grove Health", "competitive", "Full-Stack Software Engineer Intern", "internship", "ashbyhq", ["Boston, MA"]),
    ("Basalt Robotics", "competitive", "Robotics Software Intern", "internship", "lever.co", ["Pittsburgh, PA"]),
    ("Fernwood Analytics", "competitive", "Data Engineer Intern", "internship", "smartrecruiters", ["Denver, CO"]),
    ("Larkspur Bank", "competitive", "Technology Analyst Intern", "internship", "myworkdayjobs", ["Charlotte, NC"]),
    ("Copperline Energy", "competitive", "Software Developer Intern", "internship", "icims", ["Houston, TX"]),
    ("Glasswing Studios", "competitive", "Gameplay Programmer Intern", "internship", "greenhouse", ["Los Angeles, CA"]),
    ("Sable Trading", "competitive", "Software Engineer Intern, Low Latency", "internship", "greenhouse", ["New York, NY"]),
    ("Meadowlark Insurance", "accessible", "Software Engineering Intern", "internship", "myworkdayjobs", ["Des Moines, IA"]),
    ("Starling Freight", "accessible", "Application Developer Intern", "internship", "bamboohr", ["Omaha, NE"]),
    ("Pinecrest Software", "solid", "Platform Engineer Intern", "internship", "ashbyhq", ["Remote in USA"]),
    ("Wren Data", "solid", "AI Engineer Intern", "internship", "greenhouse", ["San Jose, CA"]),
    ("Cinder Cloud", "solid", "Site Reliability Intern", "internship", "lever.co", ["Portland, OR"]),
    ("Bluefin Logistics", "solid", "Software Engineer Intern", "internship", "careers", ["Atlanta, GA"]),
    ("Arbor Mobility", "solid", "Autonomy Data Intern", "internship", "ashbyhq", ["Detroit, MI"]),
    ("Halcyon Bio", "solid", "ML for Biology Intern", "internship", "greenhouse", ["Cambridge, MA"]),
    ("Driftwood Games", "solid", "Tools Engineer Intern", "internship", "workable", ["Montreal, QC, Canada"]),
    ("Ironbark Defense", "solid", "Embedded Software Intern (U.S. citizens only)", "internship", "myworkdayjobs", ["Huntsville, AL"]),
    ("Saltmarsh Labs", "solid", "PhD Research Intern, Systems", "internship", "greenhouse", ["Redmond, WA"]),
    ("Lattice Forge", "solid", "Developer Tools Intern", "internship", "ashbyhq", ["Remote"]),
    ("Quillon Security", "competitive", "Security Engineer Intern", "internship", "greenhouse", ["Washington, DC"]),
    ("Granite Peak Credit Union", "accessible", "IT Developer Intern", "internship", "paylocity", ["Boise, ID"]),
    ("Hollow Oak Media", "solid", "Frontend Engineer Intern", "internship", "lever.co", ["Brooklyn, NY"]),
    ("Redwood Assembly", "solid", "Software Engineer, New Grad", "job", "greenhouse", ["Oakland, CA"]),
    ("Open Climate Hack", "solid", "Open Climate Hack 2026", "hackathon", "devpost.com", ["Online"]),
    ("AgentJam", "solid", "AgentJam: build an agent in 48 hours", "hackathon", "devpost.com", ["Online"]),
    ("Civic Tech Weekend", "solid", "Civic Tech Weekend Hackathon", "hackathon", "lu.ma", ["Chicago, IL"]),
    ("BuildFest", "solid", "BuildFest Online", "hackathon", "devpost.com", ["Online"]),
    ("Lighthouse Foundation", "competitive", "Lighthouse Open Source Fellowship", "fellowship", "typeform.com", ["Remote"]),
    ("Founders Residency", "reach", "Summer Founders Residency", "program", "airtable.com", ["San Francisco, CA"]),
    ("Open Science Fund", "solid", "Open Science Microgrant", "grant", "docs.google.com/forms", ["Online"]),
    ("Systems Futures", "competitive", "Systems Futures Scholarship", "scholarship", "jotform", ["Online"]),
    ("AI Builders Night", "solid", "AI Builders Night: demos + pizza", "event", "lu.ma", ["San Francisco, CA"]),
]

# org -> (status, iteration, round, days since applied, [(day offset after applying, status, text)])
STORY = {
    "Tidewater Systems": ("rejected", 0, 1, 34, [(0, "applied", "Application received"), (2, "rejected", "Not moving forward (2 days)")]),
    "Glasswing Studios": ("rejected", 0, 1, 34, [(0, "applied", "Thanks for applying"), (1, "rejected", "Position filled by other candidates")]),
    "Fernwood Analytics": ("interview", 0, 1, 33, [(0, "applied", "Application received"), (9, "assessment", "Take-home data exercise, due in 5 days"), (19, "interview", "Recruiter call scheduled")]),
    "Basalt Robotics": ("applied", 0, 1, 33, [(0, "applied", "Application received")]),
    "Copperline Energy": ("rejected", 0, 2, 30, [(0, "applied", "Application received"), (17, "rejected", "Decided to move forward with others")]),
    "Meadowlark Insurance": ("assessment", 0, 2, 30, [(0, "applied", "Application received"), (0.01, "assessment", "Online assessment invite (sent automatically)")]),
    "Larkspur Bank": ("applied", 0, 2, 29, [(0, "applied", "Application received")]),
    "Starling Freight": ("offer", 0, 2, 29, [(0, "applied", "Application received"), (8, "interview", "Two 45-minute interviews"), (21, "offer", "Offer letter, decision due in 2 weeks")]),
    "Northwind Labs": ("applied", 1, 3, 12, [(0, "applied", "Thank you for applying")]),
    "Parallax AI": ("assessment", 1, 3, 12, [(0, "applied", "Application received"), (3, "assessment", "Coding assessment, 70 minutes, due Friday")]),
    "Juniper Grove Health": ("interview", 1, 3, 11, [(0, "applied", "Application received"), (6, "interview", "Technical interview booked")]),
    "Kestrel Quant": ("rejected", 1, 3, 11, [(0, "applied", "Application received"), (4, "rejected", "Not moving forward")]),
    "Vantage Research": ("applied", 1, 3, 10, [(0, "applied", "Application received")]),
    "Pinecrest Software": ("applied", 1, 3, 10, [(0, "applied", "Application received")]),
    "Orbital Works": ("saved", 1, 4, 0, []),
    "Wren Data": ("saved", 1, 4, 0, []),
    "Open Climate Hack": ("offer", 1, None, 15, [(0, "applied", "Registered"), (5, "offer", "You're in! Team matching opens Friday")]),
    "Civic Tech Weekend": ("waitlisted", 1, None, 6, [(0, "applied", "Registration received"), (2, "waitlisted", "You're on the waitlist")]),
    "Saltmarsh Labs": ("skipped", None, None, 0, []),
    # the rest of the current sitting: queued, not filled yet
    "Lattice Forge": ("", 1, 4, 0, []),
    "Cinder Cloud": ("", 1, 4, 0, []),
    "Hollow Oak Media": ("", 1, 4, 0, []),
    "Halcyon Bio": ("", 1, 4, 0, []),
}
NOTES = {
    "Fernwood Analytics": "Take-home went well; ask about the streaming team.",
    "Orbital Works": "Filled up to the review page. Needs your answer on the relocation question.",
    "Wren Data": "Cover letter attached. Waiting on the emailed security code.",
    "Saltmarsh Labs": "PhD-only posting.",
}
ANSWERS = {
    "Northwind Labs": {"Graduation date": "May 2028", "Authorized to work": "Yes", "Need sponsorship now or later": "No"},
    "Kestrel Quant": {"Graduation date": "May 2028", "GPA": "left blank (optional)", "Earliest start": "May 26"},
    "Parallax AI": {"Graduation date": "May 2028", "Start date": "June 1, 2027"},
}

CONFIG = {
    "identity": {"name": "Alex Rivera"},
    "rank": {
        "reach": [o for o, t, *_ in OPPS if t == "reach"],
        "competitive": [o for o, t, *_ in OPPS if t == "competitive"],
        "accessible": [o for o, t, *_ in OPPS if t == "accessible"],
        "fit": ["software engineer", "backend", "full[- ]?stack", "machine learning", "ml", "ai", "data", "platform",
                "developer tools", "research engineer"],
        "far": ["gameplay", "embedded", "security engineer", "analyst", "frontend"],
        "ineligible": ["phd", "master'?s", "new grad"],
        "questions": False,
    },
    "eligibility": {"requires_citizenship": ["Ironbark Defense"], "countries": ["US"]},
    "sources": [{"type": "simplify", "name": "simplify-internships"}, {"type": "devpost"}],
    "batch": {"size": 6},
}


def build(path=None, now=None):
    """Write a fresh demo database. Returns (path, config)."""
    now = now or time.time()
    path = pathlib.Path(path or pathlib.Path(tempfile.gettempdir()) / "apply-anything-demo.db")
    for p in (path, path.with_name(path.name + "-wal"), path.with_name(path.name + "-shm")):
        p.unlink(missing_ok=True)
    cfg = config.merge(config.DEFAULTS, CONFIG)
    rnd = random.Random(7)
    db = DB(path)
    rows = []
    for k, (org, _, title, kind, hint, locs) in enumerate(OPPS):
        slug = org.lower().replace(" ", "-")
        story = STORY.get(org)
        posted = now - DAY * (story[3] + rnd.randint(3, 12) if story and story[3] else rnd.randint(0, 26))
        deadline = None
        if kind in ("hackathon", "fellowship", "grant", "scholarship", "program", "event"):
            deadline = now + DAY * rnd.randint(4, 40) if not story else now + DAY * rnd.randint(8, 30)
        rows.append({"id": f"demo-{slug}", "source": "simplify-internships" if kind in ("internship", "job") else "devpost",
                     "org": org, "title": title, "kind": kind, "category": "", "locations": locs,
                     "url": f"https://example.com/demo/{hint}/{slug}", "posted_at": int(posted),
                     "deadline": int(deadline) if deadline else None, "extra": {}})
    db.upsert(rows, now)
    rank.rank(rows, cfg, fetch_questions=False, now=now)
    for r in rows:  # demo: pretend some Greenhouse forms ask for essays
        if r["platform"] == "Greenhouse" and rnd.random() < 0.4:
            r["note"] += "; 1 written answer (the agent drafts them)"
            r["effort"] = min(100, r["effort"] + 4)
    db.save_rank(rows)

    for org, (status, it, rnd_n, ago, evs) in STORY.items():
        oid = f"demo-{org.lower().replace(' ', '-')}"
        applied = now - ago * DAY if ago else None
        fields = {"status": status, "iteration": it, "round": rnd_n, "notes": NOTES.get(org, ""),
                  "answers": ANSWERS.get(org), "variant": "ml" if "ML" in org or "AI" in org else ("swe" if it is not None else None)}
        db.set_app(oid, now=applied or now, **{k: v for k, v in fields.items() if v is not None})
        for off, st, text in evs:
            db.add_event(oid, int(applied + off * DAY), st, text, source="email", msg=f"demo-{oid}-{st}-{off}", now=now)
        if applied:
            db.set_app(oid, now=now, status=status, applied_at=int(applied))
    db.set_kv("sync", {"simplify-internships": {"at": int(now - 3 * 3600), "count": 29, "added": 4, "closed": 2},
                       "devpost": {"at": int(now - 3 * 3600), "count": 9, "added": 1, "closed": 0}})
    plan, _ = batch.build(db.rows(), cfg, None, now=now)
    db.set_kv("plan", plan)
    db.close()
    return path, cfg
