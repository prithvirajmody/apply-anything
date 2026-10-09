---
name: retro
description: Retrospective on application outcomes. Works out why recent applications were rejected or advanced, updates the hypotheses and scoreboard in profile/iteration-log.md, and proposes what to change next round (resume, form answers, which opportunities to pick, outreach). Use when the user runs /retro, asks why applications were rejected, or wants to improve the next round.
---

# /retro

One turn of the loop described at the top of `profile/iteration-log.md`. Run `/refresh`
first if outcomes haven't been pulled in today.

## 1. Gather
- `./aa stats --json` for the scoreboard; `./aa export` for every application with its
  `answers`, `variant`, `iteration`, `applied_at` and events.
- Pick the outcomes the log doesn't cover yet: status rejected, assessment, interview,
  offer or waitlisted with an event newer than the last retro date in the log.
- For each: days from applying to the outcome, the platform, iteration, variant, answers.

## 2. Diagnose each outcome
- Pull the posting and its form questions (`playbooks/screening-apis.md`). If the posting is
  gone, say so.
- Compare the recorded `answers` against every knockout-style question on that form.
- Compare the posting's requirements against the resume variant that was sent.
- Classify: knockout answer · eligibility (dates, degree, authorization, GPA) · role fit ·
  skills gap · volume or ranking (a slow rejection with no other cause) · unknown. Mark the
  evidence strength.
- For advances, note what was different: variant, referral, answers, timing, tier.
- Use the signal guide in the log: ≤3 days usually means an automated knockout; an
  assessment within minutes is automatic and not a screen pass.

## 3. Update the log
- Under a new dated "Iteration N retro" heading: the per-outcome table, then each
  hypothesis's status (supported / weakened / unchanged) with the outcomes that moved it.
- Act on patterns across three or more outcomes, not single ones. Say plainly when the
  sample is too small.
- Propose changes as a table (change, hypothesis it tests, status). Changes to the resume,
  to how knockout questions are answered, or to batch order need the user's OK: ask, then
  apply. Mechanical fixes (tier lists, title keywords, packet clarifications) can be made
  directly; then tell the user.
- If anything about how forms are filled changes, bump the iteration number at the top of
  the log. Otherwise keep it: splitting one experiment into two halves each sample.

## 4. Report in chat
The scoreboard, what each new outcome most likely came from, which hypotheses moved, and
the decisions the user needs to make. The log is the long-term record.
