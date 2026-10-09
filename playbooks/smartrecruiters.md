# SmartRecruiters

No account ("oneclick" apply). The form's fields live in shadow DOM.

## Recognize it

- `jobs.smartrecruiters.com/<Company>/<posting-id>-<slug>` (the posting)
- `jobs.smartrecruiters.com/oneclick-ui/company/<Company>/publication/<uuid>...` (the form)
- `careers.smartrecruiters.com/<Company>` (the company's board)

## Flow

1. Screen with the Posting API (below).
2. Apply → the oneclick form. Upload the resume first: the resume-parse upload prefills experience and education.
3. Check and fix the prefilled sections, then fill the rest.
4. Screening questions page.
5. Hand off. The user submits.

## Field quirks

- **Shadow DOM.** `document.querySelector` won't reach most fields. Walk the `shadowRoot`s in your snippet, or use the accessibility tree.
- **Uploads:** `Runtime.evaluate` a snippet that returns the `input[type=file]` element (not by value) → its `objectId` → `DOM.describeNode(objectId=...)` → `backendNodeId` → `DOM.setFileInputFiles(backendNodeId=..., files=[PATH])`. The resume-parse upload (the `OC-APPLY-WITH-RESUME` component) is the one that prefills the profile.
- **School** is an autocomplete. Type, then click the option (formatted like "School name / City, Country"). Typed text alone doesn't count.
- **The screening page** is easiest through the accessibility tree: `Accessibility.getFullAXTree`, find the question and option nodes by name, then act on their `backendDOMNodeId` (`DOM.getBoxModel` for coordinates and a real click, or `DOM.resolveNode` for an object to click).
- **The message-to-the-hiring-team box rejects semicolons.** Rewrite them before you paste.

## Leave for the user

- Privacy and consent checkboxes, including "keep my data for future jobs".
- Demographic or legal screening questions unless the packet answers them.
- Submit.

## Screening API

```bash
curl -s "https://api.smartrecruiters.com/v1/companies/<Company>/postings/<posting-id>"
```

- `jobAd.sections` holds `companyDescription`, `jobDescription`, `qualifications` and `additionalInformation`. Also `location`, `typeOfEmployment`, `experienceLevel` and `applyUrl`.
- Every posting: `https://api.smartrecruiters.com/v1/companies/<Company>/postings?limit=100&offset=0`.
- Screening questions aren't in the public API. Read them on the form.
