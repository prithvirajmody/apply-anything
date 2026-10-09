---
name: apply
description: Fill applications in the browser for the current batch, a given batch, or one opportunity (job, internship, hackathon, fellowship, grant, program or event), using profile/packet.md as the only answer source. Fills everything up to the submit button and submits only with the user's explicit OK. Use when the user runs /apply, asks to fill or submit applications, or to work through a batch.
---

# /apply

Fill forms for the user. Everything below assumes the repo root as the working directory.

## 0. Before the first form
- Read `profile/packet.md` in full. It is the only source of answers. If it's missing,
  stop and ask the user to run `./aa init` and fill it in.
- Read `playbooks/browser-setup.md`, then start or attach to the automation Chrome it
  describes. Never use the user's everyday browser profile.
- Note the current iteration number at the top of `profile/iteration-log.md`.

## 1. Pick the work
- `/apply` alone: `./aa next --json` (the current batch). `/apply batch N`: `./aa list --batch N --json`.
  `/apply <id or org>`: `./aa show <id> --json`.
- If the user asks for a *new* batch, preview both orders first (`./aa batch --dry-run --mode prestige`
  and `--mode mixed`, plus `--mode deadline` when events or fellowships are queued), show what
  each would contain, and ask which to use. Then `./aa batch --mode <choice>`.
- Tag every opportunity you start in this sitting: `./aa set <id> --round <N> --iteration <I>`.
  The round number is one more than the highest round in `./aa list --json`.

## 2. Screen each posting before filling
Read the posting text (`playbooks/screening-apis.md` gets it without a browser for most
platforms). Skip and record the reason, with `./aa set <id> --status skipped --add-note "<reason>"`, when:
- it requires citizenship, a clearance, or work authorization the packet says the user doesn't have;
- it says it won't sponsor and the packet says the user needs sponsorship;
- fixed dates, degree level, graduation window, GPA minimum or location rule exclude the user;
- a per-company cap in the packet is already used up, or the user already applied there (`./aa list --q <org>`).

## 3. Fill
- Open the platform's playbook in `playbooks/` (by URL pattern; `playbooks/README.md` maps them).
- Pick the resume variant by the packet's rule. When a form takes a cover letter, write one
  (about 250 words, structure in `examples/profile/letters.json`), add it to a letters file in
  `profile/`, build it with `./aa letters <file> --key <key>`, check it's one page, upload it.
- Essays: one story per answer from the packet's story bank, matched to the organization.
  Rotate stories; don't reuse another organization's "why us". Respect length limits.
- Never guess. Unknown answers stay blank and go in the report.
- Leave for the user: CAPTCHAs and human checks, emailed security codes (you may find the
  email and show the user the code), signatures, attestations, legal or privacy
  acknowledgments, EEO questions the packet doesn't answer, and anything the packet marks
  "leave for me".
- Re-check every field before handing off: some platforms wipe fields after late hydration
  or after a resume parse.
- Record what you answered on every knockout-style question:
  `./aa set <id> --answer "Graduation date=May 2028" --answer "Need sponsorship=No" --variant <v>`.
- Mark it `./aa set <id> --status saved --add-note "<what's left for the user>"`.

## 4. Hand off and submit
- Report per opportunity: filled / skipped (why) / blocked (what the user must do), and the
  blank fields with the question text.
- Submit only after the user says so for that application or that batch. After each submit,
  confirm the platform's success page, then `./aa set <id> --status applied` and close the tab.
- If an answer the user gives is reusable, add it to `profile/packet.md` so it's never asked again.

## Ground rules
- One profile, truthful answers. Never invent experience, numbers, usage of a product, or
  eligibility.
- Don't let research subagents use the shared browser while forms are open.
- Don't create accounts with passwords you generate and store yourself; the user creates
  them or supplies them from their password manager.
