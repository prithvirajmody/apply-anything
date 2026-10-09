# Rippling

No account. One page. The platform supports knockout questions, and you can read them before you apply.

## Recognize it

- `ats.rippling.com/<company>/jobs/<job-uuid>`

## Flow

1. Screen first: read the embedded form JSON and look for questions marked `KNOCKOUT` (below).
2. Open the form from the job page's Apply button and upload the resume.
3. Fix what the resume parse filled in (see quirks), then fill the questions.
4. Hand off. The user submits.

## Field quirks

- **The resume parse sets location and phone.** It can take a past employer's city as your location and set the phone country code to match it. Correct both after every upload.
- **Graduation buckets** are often knockout questions. Pick by the rules in [`../docs/knockout-questions.md`](../docs/knockout-questions.md); never pick a bucket that implies a later graduation than your real one.
- **Work-authorization follow-ups** ("Are you eligible for a TN, H-1B1, E-3, or F-1 EAD visa?") are knockouts too. Never leave them blank.

## Leave for the user

- EEO questions unless the packet answers them, consents, and Submit.

## Screening API

The job page is server-rendered with Next.js, and the form definition sits in its `__NEXT_DATA__` script:

```bash
curl -s "https://ats.rippling.com/<company>/jobs/<job-uuid>" -o job.html
python3 - job.html <<'PY'
import json, re, sys
t = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', t, re.S)
job = json.loads(m.group(1))["props"]["pageProps"]["apiData"]["jobPost"]
for block in job["activeJobApplication"]["additionalQuestions"]:
    for q in block["form"]["questions"]:
        print(q["questionType"], "|", "REQ" if q["isRequired"] else "opt", "|", q["title"], "|", q.get("strChoices"))
PY
```

- `questionType` is a value such as `SHORT_ANSWER`, `DOCUMENT_UPLOAD` or `KNOCKOUT`. A `KNOCKOUT` question rejects the application automatically on a disqualifying answer.
- `jobPost` also has `description` (HTML parts), `payRangeDetails`, `workLocations`, `employmentType`, `hasAIEvaluationsEnabled` and `eeocQuestionnaireEnabled`.
