# Ashby

No account. One page, rendered by React from a form definition the page fetches over GraphQL.

## Recognize it

- `jobs.ashbyhq.com/<org>/<job-id>`; the form is at `jobs.ashbyhq.com/<org>/<job-id>/application`.
- A company careers page with `?ashby_jid=<job-id>`, or an embedded `jobs.ashbyhq.com` frame.
- Class names that start with `ashby-application-form-`.

## Flow

1. Screen first: posting API for the text, GraphQL for the questions (below).
2. Open `/application` and upload the resume. Ashby may autofill name, email, phone and links from it; re-check them.
3. Fill the fields in order. Ashby validates on submit and scrolls to the first error.
4. Re-check everything, then hand off. The user submits.

## Field quirks

- **Yes/no questions are buttons, not radios**: `button[data-option="yes"]` and `button[data-option="no"]`, with `aria-pressed`.
  - Clicking an already-pressed button un-presses it. Check `aria-pressed` first.
  - A "No" clicked on a fresh field sometimes doesn't register. Click Yes, then No, then confirm `aria-pressed="true"` on No.
- **Checkbox and radio groups** live in `[data-field-path]` divs that lack the `ashby-application-form-field-entry` class. Find a group by its `.ashby-application-form-question-title` text, then walk up to the `[data-field-path]` container.
- **A radio that shows as checked in the DOM can still fail validation.** Click the `input` itself, not its label, then submit again.
- **Location** is an autocomplete (`input.ashby-application-form-input-autocomplete`). Type, wait for the options, click one.
- **Dates** (graduation, for example) are react-datepickers that take typed `MM/DD/YYYY` followed by Enter.
- **Education history:** the year list can end before your graduation year. Tick "Still Student?" rather than pick a wrong year.

## Leave for the user

- The demographic survey (a separate section) unless the packet answers it.
- Consent and acknowledgment checkboxes, and any CAPTCHA or human check.
- Submit.

## Screening API

Posting text for every job on a board, no browser needed:

```bash
curl -s "https://api.ashbyhq.com/posting-api/job-board/<org>?includeCompensation=true"
```

Each entry in `jobs[]` has `title`, `descriptionPlain`, `location`, `secondaryLocations`, `workplaceType`, `isRemote`, `employmentType`, `jobUrl`, `applyUrl`, and `compensation` when the company publishes it.

Form questions come from the GraphQL endpoint the page itself uses:

```bash
cat > ashby_query.json <<'EOF'
{"operationName": "ApiJobPosting",
 "variables": {"organizationHostedJobsPageName": "<org>", "jobPostingId": "<job-id>"},
 "query": "query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) { jobPosting(organizationHostedJobsPageName: $organizationHostedJobsPageName, jobPostingId: $jobPostingId) { id title applicationForm { sections { title fieldEntries { ... on FormFieldEntry { id field isRequired descriptionHtml } } } } } }"}
EOF
curl -s -X POST -H 'content-type: application/json' \
  "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting" --data @ashby_query.json
```

Each field entry's `field` has `title` and `type` (`String`, `Email`, `File`, `Boolean`, `LongText`, `Location`, and others); `isRequired` marks the required ones.

The endpoint can return 403 to `curl` and scripts. When it does, run the same request with `fetch` from an open `jobs.ashbyhq.com` tab (same origin; evaluate with `awaitPromise: true`):

```js
(async () => {
  const body = { /* the same JSON as ashby_query.json */ };
  const r = await fetch('/api/non-user-graphql?op=ApiJobPosting', {
    method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body)});
  const d = await r.json();
  return d.data.jobPosting.applicationForm.sections.flatMap(s => s.fieldEntries)
    .filter(e => e.field)
    .map(e => ({title: e.field.title, type: e.field.type, required: e.isRequired}));
})()
```
