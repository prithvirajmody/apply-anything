"""SQLite store shared by the CLI, the agent skills and the UI.

Tables
  opportunities  one row per posting, hackathon, fellowship or event, from a source or added by hand
  applications   your side of it: status, notes, knockout answers given, resume variant, round
  events         dated timeline entries: confirmation email, assessment invite, interview, rejection
  kv             small JSON values: the batch plan, last sync per source, refresh state
"""
import json
import pathlib
import sqlite3
import time

STATUSES = ["saved", "applied", "assessment", "interview", "offer", "waitlisted", "rejected", "skipped", "withdrawn"]
LABELS = {"": "Not started", "saved": "Filled, not submitted", "applied": "Applied", "assessment": "Assessment",
          "interview": "Interview", "offer": "Offer / accepted", "waitlisted": "Waitlisted", "rejected": "Rejected",
          "skipped": "Skipped", "withdrawn": "Withdrawn"}
# Pipeline order. Email-driven updates only move forward along it.
LEVEL = {"": 0, "saved": 1, "applied": 2, "assessment": 3, "interview": 4, "offer": 5}
# Outcomes that can arrive from any point in the pipeline
SIDE = {"waitlisted", "rejected", "skipped", "withdrawn"}
# Statuses that mean the application went out
SUBMITTED = {"applied", "assessment", "interview", "offer", "waitlisted", "rejected", "withdrawn"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  org TEXT NOT NULL,
  title TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'job',
  category TEXT NOT NULL DEFAULT '',
  locations TEXT NOT NULL DEFAULT '[]',
  url TEXT NOT NULL DEFAULT '',
  posted_at INTEGER,
  deadline INTEGER,
  active INTEGER NOT NULL DEFAULT 1,
  extra TEXT NOT NULL DEFAULT '{}',
  effort INTEGER,
  tier TEXT,
  filler TEXT,
  platform TEXT,
  note TEXT NOT NULL DEFAULT '',
  flags TEXT NOT NULL DEFAULT '[]',
  first_seen INTEGER,
  last_seen INTEGER
);
CREATE TABLE IF NOT EXISTS applications (
  opp_id TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  round INTEGER,
  iteration INTEGER,
  variant TEXT,
  answers TEXT NOT NULL DEFAULT '{}',
  referral TEXT,
  applied_at INTEGER,
  updated_at INTEGER
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  opp_id TEXT NOT NULL,
  at INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT '',
  text TEXT NOT NULL DEFAULT '',
  link TEXT,
  thread TEXT,
  msg TEXT,
  source TEXT NOT NULL DEFAULT 'manual',
  created_at INTEGER
);
CREATE INDEX IF NOT EXISTS events_opp ON events(opp_id, at);
CREATE UNIQUE INDEX IF NOT EXISTS events_msg ON events(opp_id, msg) WHERE msg IS NOT NULL;
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

JSON_COLS = {"locations": [], "extra": {}, "flags": [], "answers": {}}
OPP_COLS = ["id", "source", "org", "title", "kind", "category", "locations", "url", "posted_at", "deadline", "extra"]
APP_COLS = ["status", "notes", "round", "iteration", "variant", "answers", "referral", "applied_at", "updated_at"]


def advance(cur, new):
    """Status after an event: forward only, except side outcomes, which can arrive at any point."""
    cur = cur or ""
    if new in SIDE:
        return new
    if new not in LEVEL:
        return cur
    if cur in SIDE:
        # a later step (an interview after a waitlist) reopens it; a stale confirmation email doesn't
        return new if cur in ("waitlisted", "skipped") and LEVEL[new] >= LEVEL["applied"] else cur
    return new if LEVEL[new] > LEVEL.get(cur, 0) else cur


def _row(r):
    d = dict(r)
    for k, empty in JSON_COLS.items():
        if k in d:
            d[k] = json.loads(d[k]) if d[k] else type(empty)()
    if "referral" in d and d["referral"]:
        d["referral"] = json.loads(d["referral"])
    if "status" in d and d["status"] is None:
        d["status"] = ""
    return d


class DB:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.path, timeout=15)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.executescript(SCHEMA)

    def close(self):
        self.con.close()

    # ---- opportunities -------------------------------------------------
    def upsert(self, rows, now=None):
        """Insert new opportunities and refresh existing ones. Returns (added ids, updated count)."""
        now = int(now or time.time())
        have = {r[0] for r in self.con.execute("SELECT id FROM opportunities")}
        added = []
        with self.con:
            for r in rows:
                vals = {k: r.get(k) for k in OPP_COLS}
                vals["locations"] = json.dumps(r.get("locations") or [])
                vals["kind"] = r.get("kind") or "job"
                vals["category"] = r.get("category") or ""
                vals["url"] = r.get("url") or ""
                if r["id"] in have:
                    # keep cached extras (form questions) that the source doesn't send
                    old = json.loads(self.con.execute("SELECT extra FROM opportunities WHERE id=?",
                                                      (r["id"],)).fetchone()[0] or "{}")
                    vals["extra"] = json.dumps({**old, **(r.get("extra") or {})})
                    sets = ", ".join(f"{k}=:{k}" for k in OPP_COLS if k != "id")
                    self.con.execute(f"UPDATE opportunities SET {sets}, active=1, last_seen=:now WHERE id=:id",
                                     {**vals, "now": now})
                else:
                    vals["extra"] = json.dumps(r.get("extra") or {})
                    cols = ", ".join(OPP_COLS)
                    self.con.execute(f"INSERT INTO opportunities ({cols}, active, first_seen, last_seen) "
                                     f"VALUES ({', '.join(':' + k for k in OPP_COLS)}, 1, :now, :now)",
                                     {**vals, "now": now})
                    added.append(r["id"])
                    have.add(r["id"])
        return added, len(rows) - len(added)

    def deactivate_missing(self, source, seen):
        """Mark a source's opportunities that weren't in this sync as no longer listed."""
        ids = [r[0] for r in self.con.execute("SELECT id FROM opportunities WHERE source=? AND active=1", (source,))
               if r[0] not in seen]
        with self.con:
            self.con.executemany("UPDATE opportunities SET active=0 WHERE id=?", [(i,) for i in ids])
        return ids

    def save_rank(self, rows):
        with self.con:
            self.con.executemany(
                "UPDATE opportunities SET effort=?, tier=?, filler=?, platform=?, note=?, flags=?, extra=? WHERE id=?",
                [(r["effort"], r["tier"], r["filler"], r["platform"], r["note"], json.dumps(r["flags"]),
                  json.dumps(r.get("extra") or {}), r["id"]) for r in rows])

    def rows(self):
        """Every opportunity joined with your application fields (status '' if none)."""
        q = ("SELECT o.*, " + ", ".join(f"a.{c}" for c in APP_COLS) +
             ", (SELECT MAX(at) FROM events e WHERE e.opp_id=o.id) AS last_event_at "
             "FROM opportunities o LEFT JOIN applications a ON a.opp_id=o.id")
        return [_row(r) for r in self.con.execute(q)]

    def get(self, oid):
        r = self.con.execute("SELECT o.*, " + ", ".join(f"a.{c}" for c in APP_COLS) +
                             " FROM opportunities o LEFT JOIN applications a ON a.opp_id=o.id WHERE o.id=?",
                             (oid,)).fetchone()
        if not r:
            return None
        d = _row(r)
        d["events"] = self.events(oid)
        return d

    def find(self, text):
        """Resolve a full id, a unique id prefix, or a unique 'org' match."""
        if self.con.execute("SELECT 1 FROM opportunities WHERE id=?", (text,)).fetchone():
            return text
        ids = [r[0] for r in self.con.execute("SELECT id FROM opportunities WHERE id LIKE ?", (text + "%",))]
        if len(ids) == 1:
            return ids[0]
        ids = ids or [r[0] for r in self.con.execute("SELECT id FROM opportunities WHERE lower(org)=lower(?)", (text,))]
        return ids[0] if len(ids) == 1 else None

    def add_manual(self, row, now=None):
        added, _ = self.upsert([row], now)
        return bool(added)

    # ---- applications --------------------------------------------------
    def set_app(self, oid, now=None, **fields):
        now = int(now or time.time())
        cur = self.con.execute("SELECT * FROM applications WHERE opp_id=?", (oid,)).fetchone()
        d = _row(cur) if cur else {"status": "", "notes": "", "answers": {}}
        for k, v in fields.items():
            if k not in APP_COLS:
                raise KeyError(k)
            if k == "answers" and v is not None:
                v = {**d.get("answers", {}), **v}
                v = {q: a for q, a in v.items() if a not in (None, "")}
            d[k] = v
        if d.get("status") in SUBMITTED and not d.get("applied_at"):
            d["applied_at"] = now
        d["updated_at"] = now
        vals = {c: d.get(c) for c in APP_COLS}
        vals["answers"] = json.dumps(vals.get("answers") or {})
        vals["referral"] = json.dumps(vals["referral"]) if vals.get("referral") else None
        vals["status"] = vals.get("status") or ""
        vals["notes"] = vals.get("notes") or ""
        with self.con:
            self.con.execute(f"INSERT INTO applications (opp_id, {', '.join(APP_COLS)}) "
                             f"VALUES (:opp_id, {', '.join(':' + c for c in APP_COLS)}) "
                             f"ON CONFLICT(opp_id) DO UPDATE SET {', '.join(f'{c}=excluded.{c}' for c in APP_COLS)}",
                             {**vals, "opp_id": oid})
        return d

    # ---- events --------------------------------------------------------
    def events(self, oid=None, limit=None):
        q = "SELECT e.*, o.org, o.title FROM events e JOIN opportunities o ON o.id=e.opp_id"
        args = []
        if oid:
            q += " WHERE e.opp_id=?"
            args.append(oid)
        q += " ORDER BY e.at DESC, e.id DESC" if not oid else " ORDER BY e.at, e.id"
        if limit:
            q += f" LIMIT {int(limit)}"
        return [dict(r) for r in self.con.execute(q, args)]

    def add_event(self, oid, at, status="", text="", link=None, thread=None, msg=None, source="manual", now=None):
        """Append a timeline event and move the application's status forward if it's a later step.

        Returns (added, status). A message id that's already recorded for this opportunity is skipped,
        so re-scanning the same inbox window is safe."""
        now = int(now or time.time())
        if msg and self.con.execute("SELECT 1 FROM events WHERE opp_id=? AND msg=?", (oid, msg)).fetchone():
            return False, None
        if thread and not msg and status and self.con.execute(
                "SELECT 1 FROM events WHERE opp_id=? AND thread=? AND status=?", (oid, thread, status)).fetchone():
            return False, None
        with self.con:
            self.con.execute("INSERT INTO events (opp_id, at, status, text, link, thread, msg, source, created_at) "
                             "VALUES (?,?,?,?,?,?,?,?,?)",
                             (oid, int(at), status or "", text or "", link, thread, msg, source, now))
        cur = self.con.execute("SELECT status, applied_at FROM applications WHERE opp_id=?", (oid,)).fetchone()
        old = (cur["status"] if cur else "") or ""
        new = advance(old, status) if status else old
        fields = {}
        if new != old:
            fields["status"] = new
        if new in SUBMITTED and not (cur and cur["applied_at"]):
            fields["applied_at"] = int(at)
        if fields:
            self.set_app(oid, now=now, **fields)
        return True, new

    def delete_event(self, eid):
        with self.con:
            return self.con.execute("DELETE FROM events WHERE id=?", (eid,)).rowcount

    # ---- kv ------------------------------------------------------------
    def kv(self, key, default=None):
        r = self.con.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(r[0]) if r else default

    def set_kv(self, key, value):
        with self.con:
            self.con.execute("INSERT INTO kv (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                             (key, json.dumps(value)))
