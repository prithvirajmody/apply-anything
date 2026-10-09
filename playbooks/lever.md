# Lever

No account. One server-rendered page.

## Recognize it

- `jobs.lever.co/<company>/<posting-id>`; the form is at `.../apply`.
- EU-hosted boards: `jobs.eu.lever.co/<company>/<posting-id>`.

## Flow

1. Screen first: the postings API for the text, the `/apply` page HTML for the questions (below).
2. Open `/apply` and attach the resume. Lever may prefill name, email, phone and current company; re-check them.
3. Fill the standard fields (`name`, `email`, `phone`, `org`, `location`, the `urls[...]` links), then the custom question cards.
4. Re-check everything, then hand off. The user submits.

## Field quirks

- **Location** (`input[name="location"]`) is an autocomplete that needs a click before typing. Click the box, type, wait, pick the option.
- **Custom questions** are named `cards[<card-id>][field<n>]`. Find each one by the `.application-label` text above it.
- **Links** are one input per site, such as `urls[LinkedIn]` and `urls[Github]`. The names vary per company; read them from the DOM.

## Leave for the user

- The EEO section (`eeo[gender]`, `eeo[race]`, `eeo[veteran]`, `eeo[disability]`) unless the packet answers it.
- Consent checkboxes (data retention, future opportunities).
- The CAPTCHA (hCaptcha) that can appear at submit, and Submit itself.

## Screening API

Posting text:

```bash
curl -s "https://api.lever.co/v0/postings/<company>/<posting-id>"
```

It returns `text` (the title), `categories` (`team`, `department`, `location`, `commitment`, `allLocations`), `workplaceType`, `descriptionPlain`, `lists[]` (requirements and responsibilities), `additionalPlain`, and `salaryRange` when published. Every posting: `https://api.lever.co/v0/postings/<company>?mode=json`. EU boards use `api.eu.lever.co`.

The questions are not in the API, but the `/apply` page is server-rendered, so `curl` works. Each custom card has a hidden input `cards[<card-id>][baseTemplate]` whose value is HTML-escaped JSON: the card's `text` plus `fields[]` with `type`, `text`, `required` and `options[].text`.

```bash
curl -s "https://jobs.lever.co/<company>/<posting-id>/apply" -o apply.html
python3 - apply.html <<'PY'
import html, json, re, sys
t = open(sys.argv[1], encoding="utf-8").read()
pat = r'value="([^"]*)"[^>]*name="cards\[[^\]]+\]\[baseTemplate\]"'
for v in re.findall(pat, t):
    card = json.loads(html.unescape(v))
    for f in card.get("fields", []):
        opts = [o.get("text") for o in f.get("options", [])]
        print("REQ" if f.get("required") else "opt", "|", f.get("text"), "|", opts)
PY
```

Lever lets employers attach auto-reject rules to answers. Read every required question before you fill. See [`../docs/knockout-questions.md`](../docs/knockout-questions.md).
