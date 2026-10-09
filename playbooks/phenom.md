# Phenom

Company-branded career sites built on Phenom. The application can be a no-account draft that exists only in its tab.

## Recognize it

- The company's own careers domain, with job pages like `/<country>/<lang>/job/<id>/<slug>` (for example `/us/en/job/...` or `/global/en/job/...`)
- Apply links with `apply?jobSeqNo=...` or `hvhapply` in the path
- Page source that loads assets from `phenompeople.com` and defines a `phApp` global

## Flow

1. Re-read the posting right before the sitting. Postings on these sites change without notice.
2. Apply. Activate the tab (`Target.activateTarget`) before the CV upload; see quirks.
3. Fill the steps in order: contact details, CV, education, then questions (graduation date, right to work, visa details, non-compete).
4. Hand off. Don't navigate away and don't close the tab: a closed tab loses the draft entirely.
5. After Submit, a post-apply form (`hvhapply?…&usecase=post`) can ask for graduation year and month, societies and awards. An online-assessment invite often follows.

## Field quirks

- **The CV upload freezes the renderer.** `DOM.setFileInputFiles` on the hidden file input freezes the page for about a minute, and for over three minutes in a background tab, before the file shows as attached. Activate the tab first, then wait. Navigating away loses the page.
- **Selects revert plain changes.** A changed `selectedIndex` is undone. Use the native value setter plus a `change` event (snippet in `browser-setup.md`).
- **Education dates** are year-only react-datepickers: click the input, then click the year.
- **How did you hear** is two-level, for example Job Board → Other.
- **Right to work** can be a plain yes/no. The visa-details paragraph comes from the packet's work-authorization section.

## Leave for the user

- The non-compete box (often required) unless the packet answers it.
- EEO questions unless the packet answers them, and privacy consents.
- Submit.
- The online assessment. An invite that arrives minutes after applying is automatic. Tell the user the deadline (often a few days away) and log it: `./aa event ID --status assessment --text "Online assessment invite, due YYYY-MM-DD"`.
