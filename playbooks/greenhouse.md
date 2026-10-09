# Greenhouse

No account. One page. Many no-account applications run on it.

## Recognize it

- `boards.greenhouse.io/<board>/jobs/<id>` (older boards)
- `job-boards.greenhouse.io/<board>/jobs/<id>` (newer boards; EU-hosted boards use `job-boards.eu.greenhouse.io`)
- `job-boards.greenhouse.io/embed/job_app?for=<board>&token=<id>` (the bare form)
- A company careers page with `?gh_jid=<id>` in the URL, or a Greenhouse iframe on the page

## Flow

1. Screen first with the boards API (below). It returns the posting and every question.
2. Open the embed URL directly: `https://job-boards.greenhouse.io/embed/job_app?for=<board>&token=<id>`. Job-board links often redirect to the company's careers page, which wraps the same form in extra frames.
3. Upload the resume first. Greenhouse parses it, and the parse wipes text fields typed earlier.
4. Fill the text fields, then the dropdowns and questions, then the cover letter if the form takes one.
5. Re-check every field (late hydration can wipe text and uploads), then hand off. The user clicks Submit.
6. If a security-code box appears after Submit, see "Leave for the user".

## Field quirks

- **Element ids usually match the API's field names**: `#first_name`, `#last_name`, `#email`, `#phone`, `#resume`, `#cover_letter`, `#question_<id>`. Map answers from `questions[].fields[].name`, and confirm in the DOM.
- **Uploads:** `DOM.setFileInputFiles` on `#resume` and `#cover_letter`. The API also lists `resume_text` and `cover_letter_text` (the "enter manually" option); leave them empty when you attach a file.
- **Dropdowns are react-selects.** Open them from the chevron, not the text area. In a fresh tab the first open often shows no options: close it and open it once more.
- **Hidden phone country-code list.** The phone field keeps a hidden list of country options in the DOM. Filter `[role=option]` to visible elements (`el.getClientRects().length > 0`), or every dropdown pick lands on "United States +1".
- **The "Country\*" select next to the phone is the phone country code**, not your country of residence.
- **Options below the menu's visible area don't take the click.** Call `option.scrollIntoView({block: 'nearest'})`, re-read its rect, click, then confirm the choice in `.select__single-value`.
- **The location (city) autocomplete** only suggests results when the text arrives one character at a time. Type the city per character, wait, then pick the option.
- **School lists use official names.** Type one distinctive word of the school's name, then pick the exact option.
- **Single-line essay fields.** Some "why us" questions are `<input>`s with `maxlength="255"`. Check `maxLength` before you write the answer.
- **Custom careers pages.** Some companies render the Greenhouse form with their own dropdown widgets. Read the DOM; the react-select rules may not apply.

## Leave for the user

- **The emailed security code.** Some boards hold the submit for an 8-character code "to confirm you're a human". It comes from `no-reply@us.greenhouse-mail.io`, subject "Security code for your application to <Company>", usually within a minute. It's an anti-bot check, so the user types it. You may find the email and show the code. Keep the tab open until the user has entered it, and meanwhile record `./aa set ID --status saved --note "waiting on security code"`.
- **Human checks**, such as "What is to the left of your computer?". Never answer them.
- **Attestations and acknowledgments**: "I acknowledge receipt of the privacy notice", AI-usage attestations, accuracy statements.
- **Demographic (EEO) questions**, unless the packet gives an answer.
- **Submit.**

## Screening API

```bash
curl -s "https://boards-api.greenhouse.io/v1/boards/<board>/jobs/<id>?questions=true"
```

- `content`: the posting text, HTML-escaped.
- `questions[]`: `label`, `required`, `description`, and `fields[]` with `name`, `type` (`input_text`, `input_file`, `textarea`, `multi_value_single_select`, `multi_value_multi_select`) and `values[]` (each option's `label` and `value`).
- `location_questions`, `compliance`, `demographic_questions`, `data_compliance`: extra sections, often empty.
- `application_deadline`, when the employer set one.
- Every job on a board: `https://boards-api.greenhouse.io/v1/boards/<board>/jobs?content=true`.

Greenhouse lets employers attach auto-reject rules to answers, so read every required yes/no and select before you fill. See [`../docs/knockout-questions.md`](../docs/knockout-questions.md).
