# Iteration log

Each round of applications is an experiment. The loop:

1. `/refresh` brings in outcomes from your inbox.
2. `/retro` works out why each rejection or advance happened: it reads each form's
   questions and the answers you recorded, checks the posting against the resume
   variant you sent, updates the hypotheses below, and proposes what to change.
3. The changes are tagged on the next round's applications (`--iteration N`,
   `--variant`, `--answer`) so iterations can be compared.

**Signal guide**
- A rejection within about 3 days almost always comes from an automated knockout rule
  on a form answer. Greenhouse, Lever and Rippling all support auto-reject rules.
- AI match scores (Greenhouse, Ashby, Workday HiredScore, Avature) rank candidates
  rather than reject them, but a recruiter may only look at the top band.
- A rejection after two weeks or more usually means a person, or the ranking, passed.
- An assessment invite that arrives within minutes of applying is automatic: everyone
  gets it, so it isn't a screen pass. `./aa stats` counts these separately as "auto".

One rejection is noise. A pattern across three or more is signal.

**Current iteration: 0**

## Scoreboard

`./aa stats` prints the live version. Copy it here at each retro.

| Iteration | Submitted | Rejected ≤3 days | Rejected later | Assessment (auto) | Interview | Offer | Pending |
|---|---|---|---|---|---|---|---|
| 0 | | | | | | | |

---

## Iteration 0: baseline

**Setup:** resume version, batch order, which knockout answers were given, cover letters
yes/no.

**Outcomes** (filled in by /retro)

| Application | Platform | Days | Most likely cause | Evidence (strength) |
|---|---|---|---|---|

**Hypotheses** (strongest first; each gets a status: supported, weakened, unchanged)
- H1. Knockout answers decide most fast rejections.
- H2. The location and phone that resume parsers read affect screening.
- H3. Roles far from your profile get screened out fast.
- H4. Materials that read as generic or AI-written hurt.
- H5. Referrals convert far better than cold applications.

**Changes for iteration 1**

| # | Change | Tests | Status |
|---|---|---|---|
