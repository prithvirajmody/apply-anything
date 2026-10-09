# Apply Anything: notes for agents

A tool for applying to things (jobs, internships, hackathons, fellowships, scholarships,
grants, programs, events). The user's data lives in `profile/`, which is git-ignored.

## Skills
- `/apply`: fill forms in the browser for a batch or one opportunity; never submit without OK.
- `/refresh`: record replies from the inbox, sync sources, rebuild batches.
- `/retro`: explain outcomes, update `profile/iteration-log.md`, propose changes.
- `/find`: search the web for opportunities and add the verified ones.

## The CLI is the interface
`./aa` reads and writes the database; add `--json` to read. Don't edit `profile/aa.db` directly.
Common: `./aa next --json`, `./aa show ID --json`, `./aa list --q ORG --all --json`,
`./aa set ID --status saved --answer "Q=A" --variant V --round N --iteration N`,
`./aa event ID --status S --text T --msg MSGID --source email`, `./aa add URL --kind K`.

## Rules
1. **Privacy.** Never copy anything from `profile/` (packet, config identity, resume or letter
   content, the database, generated files) into tracked files, commit messages, issues or PRs.
   Examples and tests use the fictional "Alex Rivera", example.com, and made-up organizations.
2. **Submit only with the user's explicit OK** for that application or that batch.
3. **Human-only steps:** CAPTCHAs and human checks, emailed security codes (find the email and
   show the code; the user types it), signatures, attestations, legal and privacy
   acknowledgments, waivers, and EEO questions the packet doesn't answer.
4. **Truthful answers only,** from `profile/packet.md`. Missing means blank plus a line in the report.
5. **Passwords** come from the user or their password manager; never generate and store them.
6. **One driver for the browser.** Research subagents use curl or fetch while forms are open.
7. Read `playbooks/browser-setup.md` before driving Chrome, and the platform's playbook before
   filling a form on it.

## Development
- Python 3.11+, standard library only. Tests: `python3 -m unittest discover -s tests` (no network).
- `./aa ui --demo` serves fictional data for UI work and screenshots.
- UI: `applyanything/ui/` (plain JS, no build step). Put data into the DOM with text nodes,
  never `innerHTML`: titles and org names come from public feeds.
- Sources: one module per type in `applyanything/sources/`, registered in `_types()`.
