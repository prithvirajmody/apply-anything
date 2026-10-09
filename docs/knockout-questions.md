# Knockout questions

A knockout question is a form question with an auto-reject rule behind it. Answer it the disqualifying way and the application is rejected at submission, before anyone reads the resume. Greenhouse, Lever and Rippling let employers set such rules, and Workday questionnaires can disqualify on an answer too. Most fast rejections come from these answers, not from the resume, so they deserve more care than any essay.

Screen for them before filling ([`../playbooks/screening-apis.md`](../playbooks/screening-apis.md)): most platforms expose the questions without a browser.

## Reading outcomes: the signal guide

| What happened | What it most likely means |
|---|---|
| A rejection within about 3 days | An automated knockout on a form answer |
| A rejection after 2 weeks or more | A person, or the ranking, passed on the application |
| Weeks of silence | Still in the pile, or ranked below the band anyone reviews |
| An online-assessment (OA) invite within minutes of applying | Automatic: everyone gets it. Not a screen pass |
| An OA or interview invite after a few days | A real screen pass |

- AI match scores (Greenhouse Talent Matching, Ashby, Workday HiredScore, Avature) rank candidates rather than reject them. A recruiter may only look at the top band, so a low rank shows up as silence or a late rejection.
- One rejection is noise. A pattern across 3 or more is a signal. The retrospective loop (`profile/iteration-log.md`) compares outcomes by answer, resume variant and iteration.

Not every fast rejection is a knockout. Two other patterns show up:

- **Off-profile roles.** A role outside the applicant's profile (an analyst, design or product-research posting for an engineering resume) tends to be screened out quickly. Spend sittings on roles the resume matches.
- **Materials that read as AI-written.** Vanity metrics (repeated test counts, lines of code) and dense jargon make a resume or an answer read as generated, and many hiring managers treat that as a red flag. Prefer plain verbs and one real number per claim.

## Record every knockout answer

For each application, record what you answered on every knockout-style question: graduation date or bucket, work authorization, sponsorship, OPT/EAD follow-ups, GPA, location, start date and program dates. Record the exact option text you picked, not a paraphrase.

```bash
./aa set ID --answer "Expected graduation=Jan–May 2030"
./aa set ID --answer "Will you now or in the future require sponsorship?=Yes"
./aa set ID --variant swe --iteration 1
./aa show ID
```

Without this record, a fast rejection can't be diagnosed.

## Graduation-date buckets

Many forms offer ranges ("Dec 2029", "Jan–May 2030", "After June 2030") instead of a date, and a graduation-window rule rejects anything outside the window the team hires for.

1. Pick the bucket that contains your real graduation month.
2. If your month falls between buckets, pick the bucket that contains the end of your final term, and give the exact date in a comments box if there is one.
3. Never pick a bucket that implies a later graduation than your real one: a later year, or an "After <month>" bucket when you finish in or before that month. A later bucket can fall outside the hiring window.

Example: your final exams end in May 2030 and the degree is conferred in June 2030. The form offers "Jan–May 2030" and "After June 2030", so June falls in the gap. Your final term ends in May, so pick "Jan–May 2030" and write "Final term ends May 2030; degree conferred June 2030" in the comments box.

If your final term also ends in the gap (a term that ends in early June, say), pick the earlier bucket, the one your final term belongs to, and explain the dates. Settle the rule with the user once, write it in the packet, and give every form the same answer.

## Start dates and program windows

- "Earliest start date": the first date after your final exams, and after any work authorization your school must approve. Keep it in the packet and use the same date everywhere.
- A form that offers only dates before you can start: leave the field blank and flag it.
- A yes/no "Can you work <fixed dates>?" that you can't meet: the honest answer is No, and it is probably a knockout. Flag the listing before filling it; the user decides whether it's still worth applying.
- Never stretch a date. A start date you can't keep surfaces at offer time.

## GPA

- Enter a GPA only when the field is required, or when the packet says to.
- A required "Is your GPA X or above?" is a knockout. Answer truthfully, and flag the listing first if the answer is No.
- Upload transcripts only with the user's OK for that application.
- Keep GPA out of essays.

## Resume parsers: location and phone

Many forms parse the uploaded resume and prefill fields. Parsers make predictable mistakes:

- **Location:** they take the first place name they find, often a past employer's or school's city, as your home location.
- **Phone:** they set the country code from that place, so a domestic number gets a foreign prefix.
- **Everything else:** junk skills, wrong dates, a job title in the company field.

Why it matters: some ATSs weigh location in their match scores, and some fraud checks compare location, phone and IP address. A wrongly parsed location can make a local applicant look remote or ineligible.

- Put your current city in the resume header, so the parser finds it first.
- After every upload, re-check location, phone, country code, school and dates against the packet, and remove junk skills.
- Upload first, then type. On some platforms the parse overwrites fields typed earlier.

## Work authorization: a worked example (F-1 student)

The wording of the question decides the answer. The table below is a worked example for a student on a U.S. F-1 visa: CPT (Curricular Practical Training) for internships during the degree, OPT after graduation (plus the STEM OPT extension for STEM degrees), and H-1B sponsorship later. Use it as a model when you write the work-authorization section of your own packet.

**Confirm every answer with your school's international student office (your designated school official, or DSO) before you use it.** This is not legal advice, the rules change, and CPT eligibility depends on your school and program.

| Question wording | Answer in this example |
|---|---|
| "Are you legally authorized to work in the U.S.?" (plain yes/no) | Yes (through CPT for internships) |
| "…authorized to work for **any** employer in the U.S.?" | No. Pick the option that says you require sponsorship |
| "Will you now or in the future require sponsorship?" | Yes |
| Multiple choice with an option naming F-1, CPT, OPT or "will require in the future" | Pick that option |
| "What type of sponsorship or visa?" | F-1 student: CPT for the internship, OPT/STEM OPT after graduation, H-1B later |
| "Eligible for OPT / STEM OPT / F-1 EAD?", or "eligible for a TN, H-1B1, E-3, or F-1 EAD visa?" | Yes. OPT is the F-1 EAD, available after graduating from a U.S. degree program, plus STEM OPT for STEM degrees. These follow-ups are knockout questions: never leave them blank |
| "Do you require **sponsorship** for this internship?" (scoped to the internship only) | No. CPT is authorized by the school, not sponsored by the employer. If the same form asks about the future, answer that question Yes |
| "Do you require **work authorization** for this internship?" | Yes. CPT is a work authorization obtained through the school. Explain in a comments box if there is one |
| "Legally eligible to begin employment immediately?" | Often No: CPT must be approved for the specific employer before work starts |
| "If you're on STEM OPT, when does it expire?" | Not applicable (on F-1, not on OPT yet) |
| "Are you a U.S. citizen?" or "Are you a U.S. person?" (export control) | No |
| "Authorized to work in <another country>?" | Usually No. Flag the listing |
| "Do you hold a security clearance?" | No |
| Visa expiry date, I-20 program end date | From the packet only. Never assume a date |

Text for an optional details box (fill in the brackets):

> F-1 student. I'll work this internship under CPT, which my university authorizes, so the internship needs no employer sponsorship. After graduating in [Month Year] I'm eligible for OPT plus the STEM OPT extension (up to 3 years of work authorization); I'd need H-1B sponsorship only after that.

Notes:

- The truthful sponsorship answer can't change, but details boxes and OPT/EAD follow-ups give the reader the full picture. Fill them whenever a form has them.
- Visa status belongs in the authorization fields. Keep it out of essays.
- STEM OPT requires a STEM-designated degree and an employer enrolled in E-Verify.

**U.S. citizens and permanent residents**, in one line: authorized to work = Yes; require sponsorship now or in the future = No; "U.S. person" for export control = Yes; "U.S. citizen" = Yes only for citizens.

## Export control and "deemed export" questions

Releasing controlled technology to a foreign person inside the U.S. counts as an export to that person's country (a "deemed export"), so some employers ask about it. The forms ask in different ways. Read the help text under the question before you answer.

- "Are you a U.S. person?" Under U.S. export rules this usually means a citizen, a permanent resident, or a protected individual (a refugee or asylee). Answer by the definition the form gives.
- Some forms define the question narrowly, such as "Are you a citizen of <a list of embargoed countries>?". Answer the question as the form defines it, from the packet's citizenship, and use the form's own list rather than one from memory.
- On Workday these often come as a chain: each answer reveals the next question after Save and Continue ([`../playbooks/workday.md`](../playbooks/workday.md)).
- Record the answers with `./aa set ID --answer "Q=A"`.

## Per-company application caps

Some large employers cap how many applications a candidate can submit in a period: per rolling month, per half-year, or a single internship application worldwide. Applications past the cap may not be considered. Check each company's careers FAQ before applying, write the cap in the packet, and spend capped slots on the best-fit roles.

## Other questions that need a packet answer

These aren't always knockouts, but a wrong guess can hurt. Answer from the packet; if it has no answer, leave the question for the user.

- **Government employee or official** (yourself or a relative). Some forms count publicly funded institutions, such as a paid job at a public university.
- **Non-compete or restrictive agreements.** Whether a confidentiality agreement counts is the user's call.
- **Criminal history and professional licenses.** From the packet only.
- **Desired compensation.** From the packet. Pick "Prefer not to disclose" only when the form offers it and the packet allows it.
- **"Referred by an employee?"** Yes only when a referral is logged (`./aa set ID --referral "Name"`), and give that name.
- **SMS or text-message consent.** The user's.
- **EEO, veteran and disability questions.** From the packet if the user put an answer there. Otherwise leave them for the user.
