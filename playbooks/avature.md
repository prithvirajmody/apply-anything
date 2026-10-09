# Avature

The account is created during the first application on each portal. A multi-step flow, often on the company's own careers domain.

## Recognize it

- `<company>.avature.net/...`
- A company careers domain whose paths include `JobDetail`, `ApplicationMethods?jobId=`, `Register`, or `Success`
- select2 widgets (`.select2-container`) and TinyMCE editors on the application pages

## Flow (first application on a portal)

1. Apply → choose where the resume comes from. Click "From Device" (or "My Computer") first, then upload:
   - with an input present: `DOM.setFileInputFiles` on `#resumeFile`, then click Next (`#uploadFileResume`);
   - if Upload opens a file chooser and no input is reachable: `Page.setInterceptFileChooserDialog(enabled=True)`, click Upload, set the file on the chooser's `backendNodeId`, then Continue.
2. The Register page creates the account. It shows the parsed work history, plain selects and a password field. The password is the user's. Some portals send no verification email.
3. About You: contact details, school, GPA (when required), demographics.
4. Role-specific questions: role, education level, graduation month, free-text answers.
5. "Are you ready to submit?" → Submit (the user). The success page's URL contains `/Success`.

## Field quirks

- **select2 lookups** (country, state, school) need about 3 seconds after typing before options appear. Poll `.select2-results__option`.
- **Some school pickers ignore typed search text.** Open the picker, scan `.select2-results__option` for the exact school name, and click it.
- **Graduation month** is an `input[type=month]`. Set the value as `YYYY-MM`, then fire `input` and `change` events.
- **Rich-text answers are TinyMCE editors.** Typing into the editor's iframe is unreliable. Set the content and sync it to the underlying textarea:

  ```js
  (() => { const ed = tinymce.get(ID); ed.setContent(HTML); ed.save(); return ed.getContent(); })()
  ```

- **The resume parser adds junk skills.** Remove anything that isn't in the packet's skill list.
- **Parsed location.** Avature's match score is reported to weigh location, so correct the parsed address and phone.

## Leave for the user

- The password on the Register page.
- Demographic dropdowns and veteran or disability radios (often required) unless the packet answers them.
- Certifications, attestations and legal acknowledgments.
- Submit.
