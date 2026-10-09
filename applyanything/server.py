"""Local web UI: a small JSON API over the database plus the static app in ui/.

Security: binds to 127.0.0.1 only; refuses requests whose Host header isn't this
server (DNS rebinding); every write needs the random per-run token embedded in the
page, sent as an X-AA-Token header, which other websites can't read or forge.
"""
import json
import pathlib
import secrets
import threading
import time
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import batch, insights, pipeline
from .db import DB, LABELS, STATUSES

UI = pathlib.Path(__file__).resolve().parent / "ui"
STATIC = {"app.js": "text/javascript; charset=utf-8", "style.css": "text/css; charset=utf-8",
          "favicon.svg": "image/svg+xml"}
SORTS = {
    "effort": (lambda r: (r.get("tier") == "ineligible", r.get("effort") is None, r.get("effort") or 0), False),
    "-effort": (lambda r: r.get("effort") or 0, True),
    "newest": (lambda r: r.get("posted_at") or r.get("first_seen") or 0, True),
    "deadline": (lambda r: r.get("deadline") or float("inf"), False),
    "org": (lambda r: (r["org"].lower(), r["title"].lower()), False),
    "updated": (lambda r: max(r.get("updated_at") or 0, r.get("last_event_at") or 0), True),
}
APP_FIELDS = {"status", "notes", "round", "iteration", "variant", "answers", "referral"}


class Job:
    """One background action (sync or re-rank) at a time, with a log the UI polls."""

    def __init__(self):
        self.lock = threading.Lock()
        self.state = {"state": "idle"}

    def start(self, action, fn):
        with self.lock:
            if self.state.get("state") == "running":
                return False
            self.state = {"state": "running", "action": action, "log": [], "started": time.time()}

        def work():
            try:
                result = fn(self.state["log"].append)
                self.state.update(state="done", result=result, finished=time.time())
            except Exception as e:
                self.state.update(state="error", error=str(e), finished=time.time())
        threading.Thread(target=work, daemon=True).start()
        return True


def filter_rows(rows, q):
    get = lambda k: (q.get(k) or [""])[0]
    text = get("q").lower().strip()
    status, tier, kind, filler = (set(filter(None, get(k).split(","))) for k in ("status", "tier", "kind", "filler"))
    flagged, show = get("flagged"), get("show")
    out = []
    for r in rows:
        st = r.get("status") or ""
        if show != "all" and not r.get("active") and not st:
            continue
        if status and not (("open" in status and not st) or st in status):
            continue
        if tier and r.get("tier") not in tier:
            continue
        if kind and r.get("kind") not in kind:
            continue
        if filler and r.get("filler") not in filler:
            continue
        if flagged == "hide" and r.get("flags"):
            continue
        if flagged == "only" and not r.get("flags"):
            continue
        if text and text not in " ".join([r["org"], r["title"], " ".join(r.get("locations") or []),
                                           r.get("notes") or "", r.get("category") or ""]).lower():
            continue
        out.append(r)
    key, rev = SORTS.get(get("sort") or "effort", SORTS["effort"])
    out.sort(key=key, reverse=rev)
    return out


def make_handler(db_path, cfg, token, port, demo=False, job=None):
    job = job or Job()
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        server_version = "apply-anything"

        def log_message(self, *args):
            pass

        # ---- plumbing --------------------------------------------------
        def send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else json.dumps(body, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if ctype.startswith("text/html"):
                self.send_header("Content-Security-Policy",
                                 "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                                 "connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}") if n else {}

        def guard(self, write):
            if self.headers.get("Host") not in hosts:
                self.send(403, {"error": "unexpected Host header"})
                return False
            if write and not secrets.compare_digest(self.headers.get("X-AA-Token") or "", token):
                self.send(403, {"error": "missing or wrong token; reload the page"})
                return False
            return True

        def route(self, method):
            path = urllib.parse.urlparse(self.path)
            parts = [urllib.parse.unquote(p) for p in path.path.strip("/").split("/") if p]
            q = urllib.parse.parse_qs(path.query)
            if not self.guard(method != "GET"):
                return
            db = DB(db_path)
            try:
                self.dispatch(method, parts, q, db)
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                self.send(400, {"error": str(e)})
            except Exception as e:
                traceback.print_exc()
                self.send(500, {"error": str(e)})
            finally:
                db.close()

        def do_GET(self):
            self.route("GET")

        def do_POST(self):
            self.route("POST")

        def do_PATCH(self):
            self.route("PATCH")

        def do_DELETE(self):
            self.route("DELETE")

        # ---- routes ----------------------------------------------------
        def dispatch(self, method, parts, q, db):
            if method == "GET" and not parts:
                page = (UI / "index.html").read_text().replace("{{TOKEN}}", token).replace("{{DEMO}}", "1" if demo else "")
                return self.send(200, page.encode(), "text/html; charset=utf-8")
            if method == "GET" and len(parts) == 2 and parts[0] == "static" and parts[1] in STATIC:
                return self.send(200, (UI / parts[1]).read_bytes(), STATIC[parts[1]])
            if not parts or parts[0] != "api":
                return self.send(404, {"error": "not found"})
            api = parts[1:]

            if method == "GET" and api == ["meta"]:
                return self.send(200, {"statuses": STATUSES, "labels": LABELS, "demo": demo,
                                       "tiers": ["reach", "competitive", "solid", "accessible", "ineligible"],
                                       "sources": [{"name": s.get("name") or s["type"], "type": s["type"]}
                                                   for s in cfg["sources"]],
                                       "batch": cfg["batch"], "identity": {"name": cfg["identity"].get("name", "")}})
            if method == "GET" and api == ["summary"]:
                return self.send(200, insights.summary(db, cfg))
            if method == "GET" and api == ["opportunities"]:
                rows = filter_rows(db.rows(), q)
                limit = int((q.get("limit") or ["100"])[0])
                offset = int((q.get("offset") or ["0"])[0])
                return self.send(200, {"total": len(rows), "rows": rows[offset:offset + limit]})
            if method == "POST" and api == ["opportunities"]:
                b = self.body()
                if not (b.get("url") or "").startswith(("http://", "https://")):
                    raise ValueError("a http(s) URL is required")
                oid, added = pipeline.add(db, cfg, b["url"], org=b.get("org") or None, title=b.get("title") or None,
                                          kind=b.get("kind") or None, deadline=b.get("deadline") or None,
                                          location=b.get("location") or None, note=b.get("note") or None)
                return self.send(201 if added else 200, {"id": oid, "added": added, "row": db.get(oid)})
            if len(api) >= 2 and api[0] == "opportunities":
                oid = api[1]
                if not db.get(oid):
                    return self.send(404, {"error": f"no opportunity {oid}"})
                if method == "GET" and len(api) == 2:
                    return self.send(200, db.get(oid))
                if method == "PATCH" and api[2:] == ["application"]:
                    b = self.body()
                    bad = set(b) - APP_FIELDS
                    if bad:
                        raise ValueError(f"unknown fields: {', '.join(sorted(bad))}")
                    if b.get("status") and b["status"] not in STATUSES:
                        raise ValueError(f"unknown status {b['status']!r}")
                    db.set_app(oid, **b)
                    return self.send(200, db.get(oid))
                if method == "POST" and api[2:] == ["events"]:
                    b = self.body()
                    at = pipeline.parse_date(b.get("date")) or int(time.time())
                    if b.get("status") and b["status"] not in STATUSES:
                        raise ValueError(f"unknown status {b['status']!r}")
                    db.add_event(oid, at, b.get("status") or "", b.get("text") or "", link=b.get("link") or None)
                    return self.send(201, db.get(oid))
            if method == "GET" and api == ["events"]:
                evs = db.events(limit=int((q.get("limit") or ["500"])[0]))
                st = (q.get("status") or [""])[0]
                return self.send(200, [e for e in evs if not st or e["status"] == st])
            if method == "DELETE" and len(api) == 2 and api[0] == "events":
                return self.send(200, {"deleted": db.delete_event(int(api[1]))})
            if method == "GET" and api == ["batches"]:
                rows = db.rows()
                by_id = {r["id"]: r for r in rows}
                plan = db.kv("plan") or {"batches": []}
                cur = batch.current(plan, rows)
                out = [{**b, "current": bool(cur and cur["n"] == b["n"]), "progress": batch.progress(b, rows),
                        "rows": [insights.mini(by_id[i]) for i in b["ids"] if i in by_id]} for b in plan["batches"]]
                return self.send(200, {**plan, "batches": out})
            if method == "POST" and api == ["actions", "batch"]:
                b = self.body()
                plan, summary = pipeline.rebatch(db, cfg, b.get("mode") or None, bool(b.get("dryRun")))
                return self.send(200, {"summary": summary, "batches": len(plan["batches"]), "mode": plan["mode"]})
            if method == "POST" and api[:1] == ["actions"] and api[1:] in (["sync"], ["rank"]):
                if demo:
                    raise ValueError("sources are off in demo mode")
                action = api[1]

                def run(log):
                    d = DB(db_path)
                    try:
                        if action == "sync":
                            return pipeline.sync(d, cfg, log=log)
                        pipeline.rerank(d, cfg, log)
                        return {}
                    finally:
                        d.close()
                started = job.start(action, run)
                return self.send(202 if started else 409, job.state)
            if method == "GET" and api == ["job"]:
                return self.send(200, job.state)
            return self.send(404, {"error": "not found"})

    return Handler


def make_server(db_path, cfg, port=8765, demo=False):
    """Bind 127.0.0.1:port (0 = any free port). Returns (server, token)."""
    token = secrets.token_urlsafe(24)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), BaseHTTPRequestHandler, bind_and_activate=False)
    httpd.server_bind()
    httpd.RequestHandlerClass = make_handler(db_path, cfg, token, httpd.server_address[1], demo)
    httpd.server_activate()
    return httpd, token


def serve(db_path, cfg, port=8765, open_browser=True, demo=False):
    httpd, _ = make_server(db_path, cfg, port, demo)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    print(f"Apply Anything UI on {url}  (Ctrl+C to stop)" + ("  [demo data]" if demo else ""))
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
