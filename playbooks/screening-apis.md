# Screening APIs

Read a posting's text and its form questions without a browser, before the sitting. Screening a whole batch this way takes minutes, and it catches disqualifiers and knockout questions before you spend time filling.

Screen again right before each sitting. Postings change: a "no visa sponsorship" line can appear days after you first read one.

## Endpoints

| Platform | Posting text | Form questions |
|---|---|---|
| Greenhouse | `GET https://boards-api.greenhouse.io/v1/boards/<board>/jobs/<id>?questions=true` → `content` | Same call → `questions[]` (`label`, `required`, `fields[].type`, `fields[].values[].label`) |
| Lever | `GET https://api.lever.co/v0/postings/<company>/<posting-id>` (EU: `api.eu.lever.co`) → `descriptionPlain`, `lists`, `additionalPlain` | `curl` the `.../apply` page; the hidden `cards[<id>][baseTemplate]` inputs hold the questions as JSON ([`lever.md`](lever.md)) |
| Ashby | `GET https://api.ashbyhq.com/posting-api/job-board/<org>?includeCompensation=true` → `jobs[].descriptionPlain` | `POST https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting` (query in [`ashby.md`](ashby.md)). On a 403, run it with `fetch` from a `jobs.ashbyhq.com` tab |
| Workday | `GET https://<tenant>.wd<N>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/job/<path>` → `jobPostingInfo.jobDescription` ([`workday.md`](workday.md)) | Not public; it appears after sign-in |
| Rippling | The job page's `__NEXT_DATA__` JSON → `jobPost.description` | Same JSON → `additionalQuestions[].form.questions[]`; `questionType: "KNOCKOUT"` marks auto-reject questions ([`rippling.md`](rippling.md)) |
| SmartRecruiters | `GET https://api.smartrecruiters.com/v1/companies/<Company>/postings/<posting-id>` → `jobAd.sections` | Not public |
| Oracle Recruiting Cloud | `GET .../hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?...` ([`oracle.md`](oracle.md)) | Not public |

Avature, iCIMS, Phenom and amazon.jobs have no recorded public API here. Read the posting page with `curl` or a fetch tool; the questions appear only in the form.

## Example: list a Greenhouse form's questions

```bash
curl -s "https://boards-api.greenhouse.io/v1/boards/<board>/jobs/<id>?questions=true" -o posting.json
python3 - posting.json <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for q in d["questions"]:
    opts = [v["label"] for f in q["fields"] for v in f.get("values", [])]
    print("REQ" if q["required"] else "opt", "|", q["label"], "|", opts)
PY
```

Required yes/no and select questions about authorization, sponsorship, graduation, location or start date are the likely knockouts. Plan their answers from `profile/packet.md` before you open the form.

## What to screen for

Read the whole posting, including the footer and any "additional information" block. Skip or flag the listing when it has:

- **Fixed start dates or a program window** you can't meet, such as a program that starts before your term ends. A yes/no "Can you work <dates>?" is a knockout.
- **A GPA minimum**, such as "3.5+" in the text or "Is your GPA 3.0 or above?" as a required question.
- **"No sponsorship" lines**, including "we can't support CPT/OPT" and "must not require sponsorship now or in the future". These rule out anyone who will need sponsorship.
- **Citizenship, clearance or "U.S. persons only"** requirements, common at defense and government contractors.
- **Local-university-only rules**, such as "must be enrolled at a university in <state or country>".
- **Degree level** (bachelor's versus master's or PhD only) and **graduation windows** ("graduating between <month year> and <month year>").
- **Program length** that collides with your school terms, such as a fall co-op or a placement that runs into the next term.
- **Location** you can't work from, and "authorized to work in <another country>" questions.
- **Required uploads** you don't have or that the user hasn't approved (transcripts, writing samples).
- **Per-company caps** on applications. Spend a capped slot on the best-fit role.
- **Unpaid or mislabeled roles**, such as an "intern" posting that is really a senior or full-time role.

Record what you find. Skip with a reason, so the decision can be reviewed later:

```bash
./aa set ID --note "Posting footer: no sponsorship, including CPT/OPT"
./aa set ID --status skipped --note "No sponsorship (posting footer)"
```

See [`../docs/knockout-questions.md`](../docs/knockout-questions.md) for how to answer the questions that remain.
