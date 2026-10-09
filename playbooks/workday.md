# Workday

One account per company (Workday calls each company a tenant). A multi-step wizard. The slowest platform to fill, so plan a sitting around it.

## Recognize it

- `<tenant>.wd<N>.myworkdayjobs.com/[<locale>/]<site>/job/<location>/<title>_<req-id>` (`N` is a small number such as 1, 3, 5 or 12)
- The apply flow adds `/apply`, then `/apply/applyManually` or `/apply/autofillWithResume`.
- `wd<N>.myworkdaysite.com/recruiting/<tenant>/<site>/...` (same platform, other host)
- `data-automation-id` attributes all over the DOM

## Flow

1. Screen with the cxs JSON (below). The questionnaire only appears after sign-in, so plan its answers from the packet first.
2. Apply → "Apply Manually" (or "Autofill with Resume") → sign in or create an account.
   - The user supplies the password (see "Accounts and passwords" in `browser-setup.md`). A terms checkbox on this page is the user's too.
   - The Create Account button needs a real mouse click on `[data-automation-id=createAccountSubmitButton]`. A JS click does nothing.
   - Some tenants email an activation link first (sender `<tenant>@otp.workday.com`); others sign you in right after Create Account. Show the link to the user.
   - Some tenants show "Sign in with email" before Create Account. Google and LinkedIn sign-in need the user's own login, which the automation profile doesn't have by design; use email.
   - Guest apply can load but fail: lookup lists return "No Items" and the page errors. Use a signed-in account.
3. Steps (names vary by tenant): My Information → My Experience → Application Questions → Voluntary Disclosures → Self Identify → Review. Click "Save and Continue" once per step.
4. On Review, check every answer, including opt-ins that may have flipped (see below). The user submits.

## Field quirks

**Typing and clicking**
- Type with `el.focus(); el.select()` followed by `Input.insertText` (see `browser-setup.md`). It works where click-then-type misses.
- Many controls ignore JS clicks. Use real mouse clicks (`Input.dispatchMouseEvent`).

**Dropdown buttons** (country, state, degree, phone type, questionnaire answers)
- They are buttons with ids like `address--countryRegion`. Click the button, then click the `[role=option]` with the right text.
- The option list can take 2–3 seconds to appear after the click. Poll for it.

**Prompt inputs** (How did you hear, phone country code, field of study, skills)
- Focus the input, type a term, press Enter. A single match auto-selects; otherwise real-click the `[data-automation-id=promptOption]` you want.
- Enter alone can auto-pick the wrong match (field of study often does this). Type, press Enter to search, then click the exact option.
- Selected values show as `[data-automation-id=selectedItem]` pills inside the input's `multiSelectContainer`. Remove a wrong one with its `DELETE_charm`.
- Two-level prompts (How did you hear → "Internet Job Board" → "Other", for example): the second-level leaves (`promptLeafNode`) need a real click near the left edge of the row. If there's no Other, pick the company's own careers-site leaf.

**Radios and checkboxes**
- Radio ids are random and change on reload. Find radios by their label text.
- Checkbox groups (role or language preferences, a major list) register on a real click on the `label`, not on the hidden input.

**Dates** are split month and year inputs (`...-dateSectionMonth-input`, `...-dateSectionYear-input`). Type each one.

**Resume:** `DOM.setFileInputFiles` on `[data-automation-id=file-upload-input-ref]`.

**My Experience**
- Work experience is often required, and the parser fills it poorly. Type each entry by hand from the packet's employment section. Keep the entries in a list in your session code so you can re-enter them after a reset.
- School can be free text or a prompt. Degree is usually a dropdown button.

**Questionnaires**
- Follow-up questions appear one at a time after each Save and Continue (export-control chains are typical). Loop: answer, Save and Continue, look for any remaining "Select One", repeat until none is left.
- Answers are saved only by Save and Continue.

**Save and Continue stays disabled**
- After a validation error the button can turn disabled and stay that way. Reloading re-enables it but wipes the step. Refill the whole step, then click once.

**The session expires mid-flow**
- Symptom: "Something went wrong… Error Code: VPS|…" after Save and Continue. Reloading signs you out.
- Fix: "Forgot your password?" → reset link from `<tenant>@otp.workday.com` → the user sets a new password → sign in. The Sign In button needs a real click on `[data-automation-id=click_filter]`, an overlay that sits over it.
- My Information and My Experience survive. Questionnaire answers don't, because they save only on Save and Continue: re-enter them.

**Review page:** AI-matching and similar opt-ins can flip (from opt-in to opt-out) between steps. Check them against what the user chose.

## Leave for the user

- The password, terms checkboxes, and activation or reset links (show them; the user acts, or asks you to open them).
- AI-screening consent (some tenants ask for HiredScore AI-screening consent) and AI-matching preferences.
- Unless the packet answers them: non-compete or restrictive-agreement questions; government-employment questions (yourself or a spouse; some forms count publicly funded institutions such as public universities); SMS consent; salary expectations.
- Voluntary Disclosures (EEO) and Self Identify (the disability form, CC-305) unless the packet answers them. If it does: CC-305 needs a name, a date and one box, and its "I do not want to answer" box needed a real click on the `input`. The terms-and-conditions consent on Voluntary Disclosures is always the user's.
- Submit.

## Screening API (cxs JSON, no sign-in)

One posting: drop the locale from the job URL and insert `/wday/cxs/<tenant>/<site>`.

```bash
URL="https://acme.wd5.myworkdayjobs.com/en-US/External/job/Remote/Software-Engineer-Intern_R123"
API=$(printf '%s\n' "$URL" | sed -E 's#^https://([^./]+)\.([^/]+)/([a-z]{2}-[A-Z]{2}/)?([^/]+)/(job/.*)$#https://\1.\2/wday/cxs/\1/\4/\5#')
curl -s -H 'accept: application/json' "$API"
```

`jobPostingInfo` has `title`, `jobDescription` (HTML), `location`, `timeType`, `jobReqId`, `canApply` (false once the posting closes) and `externalUrl`. The sed assumes the tenant in the cxs path equals the first part of the host name, which is the usual case.

Search a site:

```bash
curl -s -X POST -H 'content-type: application/json' -H 'accept: application/json' \
  --data '{"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "intern"}' \
  "https://<tenant>.wd<N>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs"
```

Each item in `jobPostings[]` has `title`, `externalPath`, `locationsText` and `postedOn`. Append `externalPath` to `https://<tenant>.wd<N>.myworkdayjobs.com/wday/cxs/<tenant>/<site>` for the details. Page with `offset`.

The questionnaire itself isn't public. Expect work-authorization, export-control, graduation and start-date questions; see [`../docs/knockout-questions.md`](../docs/knockout-questions.md).
