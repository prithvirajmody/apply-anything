# Platform playbooks

How each application platform behaves when an agent fills it over the Chrome DevTools Protocol (CDP), and what to leave for the user. One file per platform: how to recognize it, the flow, field quirks, what to leave for the user and, where one exists, a way to read the posting and its questions without a browser.

## How to use these

- Read [`browser-setup.md`](browser-setup.md) once per session, before you open the first form. Every playbook assumes it.
- Before you fill a form, find its platform in the table below and read that playbook. Match the form's URL, not just the page's: a company careers page often embeds a third-party form in a frame.
- Screen the posting first ([`screening-apis.md`](screening-apis.md)) when the platform has an API. It is faster than opening the form, and it catches knockout questions before you spend a sitting on them.
- Take every answer from `profile/packet.md`. If the packet doesn't cover a question, leave the field blank and list it in your handoff. [`../docs/knockout-questions.md`](../docs/knockout-questions.md) covers the questions that decide fast rejections.
- Fill everything up to the submit button. Submit only with the user's explicit approval for that application.
- Always leave CAPTCHAs, human checks, signatures, attestations, legal acknowledgments and EEO/demographic questions for the user, unless the packet explicitly gives an answer.
- Record the result with an ID copied from `./aa list` or `./aa next` output, never one typed from memory:
  `./aa set ID --status saved --note "Filled; waiting on the emailed security code"`.
- When you learn a new quirk, add it to the platform's file as one bullet: the symptom, the selector, the fix. Describe how the platform behaves, not what happened at a particular employer.

These playbooks are reference material for the `apply` skill (`.claude/skills/apply/SKILL.md`).

## Platforms

| Platform | How to recognize it (URL patterns) | Account needed? | Playbook |
|---|---|---|---|
| Greenhouse | `boards.greenhouse.io/<board>/jobs/<id>`, `job-boards.greenhouse.io/<board>/jobs/<id>`, `.../embed/job_app?for=<board>&token=<id>`, a company page with `?gh_jid=<id>` | No | [greenhouse.md](greenhouse.md) |
| Ashby | `jobs.ashbyhq.com/<org>/<job-id>` (form at `/application`), a company page with `?ashby_jid=<id>` | No | [ashby.md](ashby.md) |
| Lever | `jobs.lever.co/<company>/<posting-id>` (form at `/apply`), `jobs.eu.lever.co/...` | No | [lever.md](lever.md) |
| Workday | `<tenant>.wd<N>.myworkdayjobs.com/[<locale>/]<site>/job/...`, `wd<N>.myworkdaysite.com/recruiting/<tenant>/<site>/...` | Usually; one account per company | [workday.md](workday.md) |
| Avature | `<company>.avature.net/...`, or a company careers domain with `JobDetail`, `ApplicationMethods?jobId=`, `Register` in the path | Yes, created during the flow | [avature.md](avature.md) |
| iCIMS | `careers-<company>.icims.com/jobs/<id>/<slug>/job`, `<company>.icims.com/jobs/...`; form inside `#icims_content_iframe` | Yes, created during the flow | [icims.md](icims.md) |
| SmartRecruiters | `jobs.smartrecruiters.com/<Company>/<posting-id>-<slug>`, form at `jobs.smartrecruiters.com/oneclick-ui/...` | No | [smartrecruiters.md](smartrecruiters.md) |
| Phenom | A company careers domain with `/<country>/<lang>/job/<id>/...`, apply links with `apply?jobSeqNo=` or `hvhapply`; assets from `phenompeople.com` | Varies; often none (the draft lives in the tab) | [phenom.md](phenom.md) |
| Oracle Recruiting Cloud | `<pod>.fa.<region>.oraclecloud.com/hcmUI/CandidateExperience/<lang>/sites/<site>/job/<id>` | No (email only) | [oracle.md](oracle.md) |
| Rippling | `ats.rippling.com/<company>/jobs/<job-uuid>` | No | [rippling.md](rippling.md) |
| amazon.jobs | `amazon.jobs/<lang>/jobs/<id>/...`, sign-in at `passport.amazon.jobs` | Yes ("Amazon A to Z" sign-in) | [amazon-jobs.md](amazon-jobs.md) |
| Luma, Partiful, Cerebral Valley | `lu.ma/<slug>`, `luma.com/<slug>`, `partiful.com/e/<id>`, event pages on `cerebralvalley.ai` | Luma: no. Partiful: SMS code. Cerebral Valley: emailed code | [event-platforms.md](event-platforms.md) |
| Any of the above, before filling | Posting text and form questions without a browser | No | [screening-apis.md](screening-apis.md) |

A platform that isn't listed: treat it like the closest match, read the DOM before acting, and start a new playbook from what you learn.
