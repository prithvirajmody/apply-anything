# amazon.jobs

Amazon's own careers site. An account is required, and sign-in runs through "Amazon A to Z".

## Recognize it

- `amazon.jobs/<lang>/jobs/<id>/<slug>` (the posting)
- `passport.amazon.jobs` (sign-in), followed by the Amazon A to Z identity pages (`idprism` in the URLs)

## Flow

1. Sign in: `passport.amazon.jobs` → email → "transition your account" (older accounts) → legal name → a 6-digit code emailed by `noreply@portal-na.idprism-auth.amazon.dev` → password.
   - The code expires in about 3 minutes. Find it quickly and show it to the user, who enters it.
   - The password is the user's.
2. "Complete application" opens a new tab. Attach to it.
3. The pages run: job questions → Work Eligibility → Resume (`#resume_file_input`) → Acknowledgement → EEO → Veteran (4 questions) → Review → an AI-preference modal (`#consent-yes` / `#consent-no`) → Submit.

## Field quirks

- **Dropdowns are select2.** Set them through jQuery: `jQuery(SEL).val(VALUE).trigger('change')`.
- **Dates are bootstrap datepickers.** Typed text gets cleared. Use `jQuery(EL).datepicker('setDate', new Date(YYYY, MM - 1, DD))` (JavaScript months start at 0).
- **Free-text limits are tight**, some as low as 200 characters. Count before you type.
- **"Second choice season" is required** on internship forms. Picking the same season again works.

## Leave for the user (unless the packet answers it)

- Work Eligibility questions:
  - applied before;
  - non-compete;
  - "legally eligible to begin employment immediately?" (for a student whose school must approve work authorization first, the honest answer may be No; see [`../docs/knockout-questions.md`](../docs/knockout-questions.md));
  - government employee (this form counts publicly funded institutions, so a paid job at a public university can count).
- The Acknowledgement page (accuracy, assessment integrity, at-will employment). Always the user's.
- The EEO and Veteran pages.
- The AI-preference modal.
- Submit.
- Online assessments. They usually arrive within days and are sent automatically, so an invite isn't a screen pass.

## Notes

- Check the jobs FAQ for any limit on active applications, and spend applications on the best-fit roles.
