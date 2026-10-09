# Event platforms: Luma, Partiful, Cerebral Valley

Registrations for hackathons, meetups and demo days. Track them like applications: `./aa add URL --org ... --title ... --kind hackathon --deadline YYYY-MM-DD`, then `./aa set ID --status applied` once the user has registered.

## Before any registration

- Check the event's date and city on the event page itself. Search results can point at a past event that was renamed or reused.
- Note whether the host must approve registrations, and read the host's questions before you start.

## Luma

- Recognize it: `lu.ma/<slug>`, `luma.com/<slug>`.
- Guest registration (name and email, no code) works without signing in.
- Events that require approval end in a pending state. Log the registration as `applied` and wait for the approval email.
- A "This calendar has been suspended" toast means the host's calendar is blocked, and registration is impossible. Mark it `skipped` with a note.

## Partiful

- Recognize it: `partiful.com/e/<id>`.
- Sign-in is by an SMS code sent to the user's phone. The user does it.
- Host questionnaires often require consent dropdowns (with "I agree" as the only option), a resume link (such as a cloud-drive share link), and a referral's name and email. Leave all three for the user.

## Cerebral Valley

- Recognize it: event pages on `cerebralvalley.ai`.
- Sign-in is by an emailed 6-digit code. Find it and show it to the user, who enters it.
- The application runs as a chatbot, not a form. Answer from the packet, one message per question. Pressing Escape closes the chat panel; reopen it to continue.
- The last step is an event waiver: a liability release plus a perpetual license to anything you share at the event. The user reads and accepts it.

## Leave for the user

- SMS and emailed codes, consents, waivers, resume-sharing links, and referral contacts.
- The final Register or Submit click.
