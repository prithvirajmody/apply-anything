# Applicant packet

The single source of truth for every form the agent fills for you. The agent uses only
what is written here or on your resume. When a question isn't covered, it leaves the
field blank and asks you. Update this file whenever you answer something new, so the
next form gets it right without asking again.

Replace every `<...>` placeholder. Delete rows that don't apply to you.

**Hard rules**
- Never click Submit, or anything that finalizes an application, without my explicit OK
  for that specific application (or for a named batch: "submit batch 7").
- Never invent facts, numbers, product usage or experiences. Missing information means
  a blank field and a line in the report.
- Always leave these to me: signatures and typed-name signatures, certifications and
  attestations, privacy or legal acknowledgments, CAPTCHAs and "are you human" checks,
  emailed security codes (find the email and show me the code; I type it), and any
  question this packet says to leave.
- Resume to upload: `profile/files/<variant>/<Your_Name>_Resume.pdf`. Pick the variant by
  role family: `<swe>` for software, backend, full-stack; `<ml>` for AI/ML, data, research
  engineering; `<other>` for ... Every variant uses the same file name.
- Record every knockout-style answer (graduation date or bucket, work authorization,
  sponsorship, GPA, location, start date) with
  `./aa set <id> --answer "Question=Answer"`, plus `--variant <variant>` and
  `--iteration <N>` (from `profile/iteration-log.md`). Without this, a rejection can't
  be diagnosed. When someone refers me, also `--referral "<Name>"`, and answer
  "Referred by an employee?" with Yes and that name.

---

## 1. Identity and contact

| Field | Value |
|---|---|
| First name | <First> |
| Last name | <Last> |
| Preferred name | <Preferred> |
| Email | <you@example.com> |
| Phone | <+1 555 010 0199> |
| LinkedIn | <https://www.linkedin.com/in/...> |
| GitHub / website | <https://github.com/...> |
| Pronouns | <fill only when asked, or "leave blank"> |
| Legal full name | <as on government ID, for "legal name" fields only> |

## 2. Mailing address

Forms only. Never put the street address on the resume.

| Field | Value |
|---|---|
| Address line 1 | <...> |
| Address line 2 | <...> |
| City / State / ZIP | <...> |
| Country | <...> |
| "Location (City)" autocomplete | <City, State, Country> |

## 3. Education

| Field | Value |
|---|---|
| School | <exact official name; note how its autocomplete spells it> |
| Degree / major / minor | <B.S., Computer Science, none> |
| Enrollment start | <Month Year> |
| Expected graduation | <Month Year>. Bucketed choices: pick the bucket that contains this month. If it falls between two buckets, pick the one containing the end of your final term and explain in a comments box. Never pick a bucket that implies a later year. |
| Year in school | <e.g. third year (junior)> |
| GPA | <x.xx>. Enter it only when the form won't submit without it; leave optional GPA fields blank. Or: always enter it. |
| Relevant coursework | <only if asked> |

## 4. Work authorization

Answer by how the question is worded. Fill this table for your situation. For a worked
example (a student on a US F-1 visa), see `docs/knockout-questions.md`.

| Question wording | Answer |
|---|---|
| "Are you legally authorized to work in <country>?" | <Yes / No> |
| "…authorized to work for any employer…?" | <...> |
| "Will you now or in the future require sponsorship?" | <...> |
| Optional details box on visa status | <one or two sentences, or "leave blank"> |
| "Are you a citizen / 'U.S. person' (export control)?" | <...> |
| Security clearance held? | <...> |
| Country of citizenship (if required) | <...> |

**Per-company caps.** Some employers limit how many applications you can have open or
send per period. Note the ones you know, and spend them on the best-fit role:
- <Company: N per period>

**Skip and flag** (don't fill): <e.g. postings requiring citizenship or a clearance;
postings that say they don't sponsor, if you need sponsorship>.

## 5. Standard answers

| Question | Answer |
|---|---|
| Willing to relocate? | <...> |
| Available full-time and on-site for the program dates? | <...> |
| Earliest start date | <date>. If a form only offers earlier dates, leave it blank and flag it. |
| Worked for this company before? / Related to an employee? | <No / No> |
| How did you hear about us? | <"Online job board", or "Other: <source>"> |
| May we contact your current employer? | Leave for me |
| Can you perform the essential functions, with or without accommodation? | <Yes> |
| Accommodation needed? | Leave blank |
| Desired salary / compensation | <"Prefer not to disclose" when offered; otherwise leave for me> |
| SMS / text consent | Leave for me |
| Non-compete or restrictive agreement? | <No / leave for me> |
| Gender, race/ethnicity, veteran, disability (EEO) | <your answers, or "leave for me"> |
| Criminal history questions | <your answers, or "leave for me"> |
| Government official or employee (self or relative)? | <...> |
| Test scores (SAT/ACT/GRE) | <score, or "don't enter"> |
| Transcript upload | Only with my OK per application |
| References | Leave for me |

## 6. Employment history

Newest first. Use these exact names, titles and dates in work-history sections.

1. **<Organization>**: <Title>. <Mon Year> – <Mon Year or present>. <City, State>.
   - Description: *<two or three sentences, the same facts as the resume>*
   - Limits: <e.g. under NDA: keep it general; no internal names or numbers>

Supervisor names and employer phone numbers: <provide, or leave blank and list in the report>.

## 7. Skills

<Comma-separated list. The agent adds nothing that isn't on this list.>

---

## 8. Essays and short answers

### 8a. What forms usually ask

| Type | How often | Notes |
|---|---|---|
| Why this company / what excites you | Most common | Needs one checkable fact about them |
| Project or accomplishment you're proudest of | Common | One story, one real number |
| Something not on your resume | Occasional | Personal, specific |
| Technical or scenario prompt | Occasional | Answer the question first |
| Behavioral (ownership, failure, conflict) | Occasional | Situation, action, result |
| How you use AI tools | Growing | Concrete, honest |
| Career plans / why this field | Occasional | Two sentences |

### 8b. Story bank: one story per answer

| Story | Best for | Key facts you can use | Limits |
|---|---|---|---|
| <Project or job> | <roles / question types> | <what you built, the hard part, how you knew it worked, one number> | <NDA, "simulation only", "no placement", ...> |
| <...> | | | |

### 8c. What to include
- One concrete story per answer, with one real number: what you built, what was hard,
  how you knew it worked.
- Rotate stories across applications; lead with the one that matches the organization.
- "Why us" answers connect one real, checkable thing about them (a product, a technical
  problem, a line from the posting) to one thing you've actually done.
- Answer the question they asked in the first sentence.
- Respect stated lengths. With no limit, aim for 80–150 words.
- Plain first person, specific verbs (built, traced, cut, shipped).

### 8d. What to leave out
- Visa or sponsorship details (they belong in the authorization fields), and GPA.
- Invented product usage ("I use X every day") unless I confirmed it for that company.
- Claims about the organization that aren't on their site or in the posting.
- Filler: "passionate", "leverage", "cutting-edge", flattery, restating the resume.
- Skills not in section 7, overstated depth, or negative remarks about anyone.

### 8e. Still needed from me
1. <open questions the agent has hit; strike them through once answered>

### 8f. Drafts
<Approved drafts, so later forms can reuse the good parts. Note which organization each was for.>

---

## 9. Hackathons, fellowships, programs and events

| Question | Answer |
|---|---|
| Team status / looking for teammates? | <...> |
| What will you build / why this program? | <draft per event; see 8c> |
| Portfolio, Devpost, GitHub | <links> |
| T-shirt size | <...> |
| Dietary restrictions | <or "leave for me"> |
| Travel or reimbursement needs | <...> |
| Emergency contact | Leave for me |
| Liability waivers, photo releases, codes of conduct | Leave for me |
