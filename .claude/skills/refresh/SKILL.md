---
name: refresh
description: Refresh the tracker. Scans the user's email for application responses (confirmations, assessments, interviews, rejections, offers, waitlists, acceptances) and records them, pulls the newest opportunities from every configured source, and rebuilds the batches. Use when the user runs /refresh or asks to check for responses or update the tracker.
---

# /refresh

Steps in order: the email scan changes statuses, and the rebuild needs them.
State lives in the database; `./aa` is the only interface (add `--json` to read).

## 1. Responses from email
Needs an email tool (for example a Gmail connector). If none is available, skip to step 2
and say so in the report.

- **Window:** from the last scan minus one day. `./aa export` includes the `refresh` key
  if a previous run saved it; otherwise use the last 30 days.
- **Search** (paginate; read full threads only when the snippet isn't conclusive):
  - ATS senders: greenhouse, lever, ashbyhq, myworkday / workday, icims, smartrecruiters,
    jobvite, eightfold, avature, oraclecloud, taleo, successfactors, rippling, bamboohr.
  - Assessments: codesignal, hackerrank, hirevue, karat, codility, coderpad.
  - Events and programs: devpost, lu.ma / luma, partiful, eventbrite, typeform.
  - Phrases: "thank you for applying", "application received", "next steps", "interview",
    "assessment", "unfortunately", "not moving forward", "offer", "you're in",
    "accepted", "waitlist".
  - Ignore newsletters, job-alert digests and marketing.
- **Match** each email to an opportunity by org (and title when the org has several):
  `./aa list --q "<org>" --all --json`. Never guess between two roles at one org; list those
  under "Needs a look". An email for something untracked: `./aa add <url>` if the email links
  the posting, otherwise list it.
- **Classify:**

  | Email says | Status |
  |---|---|
  | Application received / thanks for applying / registration received | applied |
  | Online assessment, coding challenge, HireVue, take-home | assessment |
  | Scheduling a call or interview | interview |
  | Offer, "you're in", accepted, admitted | offer |
  | Waitlisted | waitlisted |
  | "Unfortunately", not moving forward, position filled | rejected |

- **Record** each one: `./aa event <id> --status <s> --text "<one line, incl. any deadline>"
  --date <YYYY-MM-DD> --msg <message id> --thread <thread id> --link <email url> --source email`.
  The CLI skips messages it already has and only moves statuses forward (a rejection can come
  from anywhere), so re-scanning is safe. Also record confirmations for things already
  `applied`, so each timeline is complete.
- For assessments and interviews with a deadline or time, offer to add a calendar event.

## 2. New opportunities
`./aa sync` pulls every source, re-ranks, and rebuilds the unstarted batches. It prints, per
source, how many are open, new, and no longer listed, plus new orgs that aren't in any tier
list. Decide a tier for the notable ones (well known or very selective: reach or competitive;
small or regional: accessible; defense or clearance work: requires_citizenship), add them to
`profile/config.toml`, and run `./aa rank`.

Flag any `saved` application whose listing is no longer listed: the posting may have closed.

## 3. Report (in chat, brief)
- **Responses:** "Org, role: old → new (date)", grouped as offers / interviews / assessments
  (with deadlines) / waitlists / rejections / confirmations. Then "Needs a look".
- **Opportunities:** totals per source, new since last sync, closed, tier additions.
- **Next batch:** `./aa next` (number, orgs, minutes).
- Anything waiting on the user (`./aa list --status saved`).
- If there are new rejections or advances, suggest `/retro`.
