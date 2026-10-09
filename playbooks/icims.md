# iCIMS

The account is created during the flow. The form runs inside an iframe.

## Recognize it

- `careers-<company>.icims.com/jobs/<id>/<slug>/job` (also `.../login`, `.../candidate`)
- `<company>.icims.com/jobs/...`
- A company careers page that embeds `#icims_content_iframe`

## Flow

1. Open the job and click Apply. The form lives in `#icims_content_iframe`. It is same-origin, so drive it through `document.querySelector('#icims_content_iframe').contentDocument`.
2. First page: email, a privacy-policy select and a checkbox. Fill the email. The privacy acceptance is the user's, unless the packet says otherwise.
3. The profile page creates the account (login = email; the password is the user's), then asks for contact details, education and the resume.
4. Questions, then the EEO and veteran/disability pages.
5. A final "Portal Specific Forms" step can load in a frame from another origin (such as `<company>.icims.com/forms`).
6. Hand off. The user submits.

## Field quirks

- **Real clicks inside the iframe** need the iframe's offset: `x = frameRect.left + elRect.left + elRect.width / 2`, and the same for `y`.
- **Most selects** take `value` plus a `change` event (`el.dispatchEvent(new Event('change', {bubbles: true}))`).
- **Lazy dropdowns** (SMS consent, for example) only accept the widget: click `#<id>_icimsDropdown`, then `#result-selectable_<id>_<n>`.
- **The "Portal Specific Forms" frame** is cross-origin, so `contentDocument` is `null`. Find the frame's id with `Page.getFrameTree`, create a context with `Page.createIsolatedWorld(frameId=FRAME_ID)`, then run `Runtime.evaluate(expression=..., contextId=CTX)` inside it. This works because both origins are on `icims.com` (same site). A frame from an unrelated site runs as its own target; attach to it with `Target.attachToTarget` instead.

## Leave for the user

- The privacy-policy acceptance on the first page, and the account password.
- SMS consent unless the packet answers it.
- EEO and veteran/disability forms unless the packet answers them. The veteran form's signature checkbox is always the user's.
- Any e-signature, and Submit.
