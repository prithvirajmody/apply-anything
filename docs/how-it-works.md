# How it works

## Pieces

```
sources/*.py ──> pipeline.sync ──> db (SQLite) <── cli.py (./aa) <── Claude Code skills
                       │              ▲   ▲
                    rank.py       batch.py  server.py + ui/ (dashboard)
```

- **Sources** return plain rows. **`pipeline.sync`** stores them, marks a source's rows
  that disappeared as no longer listed, and re-ranks everything.
- **`rank.py`** scores rows; **`batch.py`** plans sittings. Both are pure functions over rows
  plus `config.toml`, which makes them easy to test and to change.
- **`db.py`** is the only thing that writes SQLite. The CLI, the UI and the agent all go through it,
  so the rules (forward-only statuses, event dedupe) hold everywhere.
- **Skills** in `.claude/skills/` tell Claude Code how to use the CLI, the browser and your
  packet. **Playbooks** in `playbooks/` hold per-platform form knowledge.

## Data model

| Table | Holds |
|---|---|
| `opportunities` | id, source, org, title, kind, category, locations, url, posted_at, deadline, active, extra (source-specific, plus cached form questions), and the ranking fields: effort, tier, filler, platform, note, flags |
| `applications` | your side: status, notes, round, iteration, variant, answers (question → answer), referral, applied_at, updated_at |
| `events` | timeline entries: at, status, text, link, thread, msg (unique per opportunity), source |
| `kv` | the batch plan, last sync per source |

Ids are prefixed by source type (`simplify-…`, `gh-<board>-<job>`, `lever-…`, `ashby-…`,
`devpost-…`); hand-added URLs get `m-<hash>` unless they are a known ATS posting, in which
case they get the same id a feed would give them, so a later sync doesn't duplicate them.

**Statuses:** saved (filled, not submitted) → applied → assessment → interview → offer.
Waitlisted, rejected, skipped and withdrawn can happen at any point. Events only move a
status forward, except those side outcomes; a waitlist or skip can be reopened by a later
step, a rejection can't be undone by a stale confirmation email. `./aa set` and the UI set
statuses directly, for corrections.

## Ranking

For each row:

1. Tier from the org lists (`reach`, `competitive`, `accessible`; anything else is `solid`).
2. Effort = tier base (82 / 62 / 42 / 24), −8 if the title matches `fit` and not `far`,
   +10 if it matches `far`, +4 for an account portal, +4 per required essay, +8 for a required
   cover letter. Clamped to 0–100.
3. Platform and filler from the URL (`platforms.py`).
4. For Greenhouse postings, the form is read once from the public boards API and cached:
   required essays, required cover letter, and the board's own title (aggregators sometimes
   relabel roles).
5. Flags: `citizen`, `no-sponsor` (only when `needs_sponsorship = true`), `location` (no
   location in `countries`, for the kinds in `location_kinds`), `closed` (deadline passed).
   Titles matching `ineligible` (for the role or the board title) become tier `ineligible`, effort 0.

## Batching

See the docstring at the top of `applyanything/batch.py`. In short: rounds (apps you tagged
with `--round`) become frozen batches; batches you've started are kept; everything else is
re-planned from the open pool on every sync, one opportunity per org, in the chosen mode.
Minutes per batch are estimates of *your* time: about 4 for a form the agent fills alone, 12
for an account portal, 10 for an unknown portal, +5 per essay, +8 for a cover letter.

## The dashboard's security model

The server binds to `127.0.0.1` only. Two guards keep other websites in your browser from
using it:

- **Host check.** Requests whose `Host` header isn't `127.0.0.1:<port>` or `localhost:<port>`
  are refused, which blocks DNS-rebinding attacks.
- **Write token.** Each run generates a random token and embeds it in the page. Every write
  needs it in an `X-AA-Token` header. Other origins can't read the page to learn it, and a
  custom header can't be sent cross-origin without a CORS preflight the server never approves.

The page has a strict Content-Security-Policy (no inline scripts), and all data reaches the
DOM as text, never as HTML, because titles and org names come from public feeds. Links are
limited to `http(s)` and `mailto`.

## Adding a source

Create `applyanything/sources/<type>.py`:

```python
from . import get_json, title_filter

def fetch(src):
    keep = title_filter(src)             # honors include / exclude
    rows = []
    for item in get_json("https://example.org/api/opportunities"):
        if keep(item["name"]):
            rows.append({"id": f"<type>-{item['id']}", "org": item["org"], "title": item["name"],
                         "kind": "fellowship", "category": "", "locations": [item.get("location", "")],
                         "url": item["url"], "posted_at": None, "deadline": None, "extra": {}})
    return rows
```

Register it in `_types()` in `applyanything/sources/__init__.py`, then use it in
`config.toml` as `[[sources]] type = "<type>"`. Add a test with a saved sample response;
tests never hit the network.
