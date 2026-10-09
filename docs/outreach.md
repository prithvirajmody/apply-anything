# Outreach: referrals and founder emails

A referral is the biggest lever outside the application itself. Referred candidates reach interviews at far higher rates than cold applicants; recruiting-platform reports have put the gap near ten times. For internships the effect is smaller, but it is still large.

In this doc, "you" is the applicant. An agent may research contacts and draft messages in the applicant's voice, but only the user sends: the user reviews, edits and sends every message, connection request and email. An agent never sends anything.

## What works, in order

1. **People who already know you.**
2. **Alumni of a school you share**, asked for a 15-minute chat.
3. **A specific note to an engineer or manager** on a team that matches one of your projects.

Two things are net negative: cold-asking strangers for a referral, and mass-messaging recruiters.

## The process

1. **List 3–5 people per target company.** Aim for at least one warm contact. Where to look is below.
2. **Message them.**
   - People you know: ask for the referral directly (template A).
   - Everyone else: ask for a 15-minute chat about their work (templates B, C, E). Don't mention a referral yet.
3. **After a good chat, ask**: "Would you be comfortable referring me for [role]?" (template D). Send the job link and ID, the resume PDF and the blurb below, so it takes them two minutes.
4. **Timing.**
   - Best case, the referral goes in before you submit, or on the same day.
   - Many systems, Greenhouse included, still link a referral to an application that's already submitted. Keep asking people you reach after applying.
   - Don't hold back a time-sensitive application while you wait for a referral.
5. **Log every contact**, and record submitted referrals (see "Logging" below). The retrospective compares referred and cold outcomes.

Expect roughly a 20–40% reply rate on alumni and team notes. Five or six thoughtful messages per company beat twenty generic ones.

## Where to find people

The user does this in their everyday browser, signed in to LinkedIn there, not in the automation profile.

- **Alumni at a company:** your school's LinkedIn page → People (alumni) → type the company in the search box. Do the same for any earlier school you attended.
- **Second-degree connections:** People search → Current company = the company → Connections = 2nd. Ask the mutual connection for an introduction instead of messaging cold.
- **Your own circles:** clubs, labs, past teams and employers, hackathon teammates and organizers, professors and teaching staff. Ask them who has gone where.
- **Team-matched engineers:** people whose posts, talks or profiles mention the team or product in the posting.

## Templates

Edit the brackets and keep each message short.

**A. Someone who knows you**

> Hey [Name]! Hope [the internship / the semester / something specific] is going well. I'm applying to [Company]'s [Role] for [season year] ([job link]), and I'd be really grateful if you'd refer me, if you're comfortable with that. I can send my resume and a two-line blurb so it takes you a minute. Totally fine if it's not something you can do!

**B. LinkedIn connection note to an alum** (keep it under 200 characters; LinkedIn limits note length, and free accounts get less room)

> Hi [Name], I'm a [year] [major] student at [school] ([shared school/club] too), applying for [Company]'s [role]. Would you have 15 minutes to talk about working on [team or area]?

**C. Follow-up once they accept**

> Thanks for connecting, [Name]! Quick context: I'm a [year] [major] student at [school]. [One proof point that matches their team, in one sentence.] I'm applying to [Company]'s [Role] and would love to understand [one specific question about their team or work]. Would 15 minutes sometime this week or next work? More about my work: [site link]

**D. After a good chat: the referral ask**

> Thanks again for the time today. [One specific thing you learned] was really helpful. If you're comfortable with it, I'd be grateful for a referral for [Role] ([job link], ID [job ID]). I've attached my resume, and here's a short blurb you can paste: "[blurb]". Either way, I really appreciated the advice.

**E. Engineer or manager on a matching team** (cold, so ask for advice, not a referral)

> Hi [Name], I saw [their post / talk / team page] on [topic]. I've been working on something close to it: [one proof point, one sentence]. I'm applying to [Company]'s [Role] and would value 15 minutes of your perspective on [specific question]. No worries if you're swamped.

**Referral blurb** (for the referrer to paste)

> [Your name] is a [year] [major] student at [school] (graduating [Month Year]) who [builds X end to end / one-line summary]. [They] built [project 1: what it does, for whom, stack], [project 2, with one real number], and [a leadership or team fact]. Applying for [Role], [job ID].

## Direct-to-founder email (small startups)

At a small startup, a short email to a founder can stand in for a formal application. A founder's reply that leads to an application counts as a referral.

**How each draft is built**

1. **One checkable hook** from the company's own public pages: the product page, a launch post, the blog, the docs or a job post. Check it against the live page on the day the draft is written. Make no claim about the company that isn't on its own pages.
2. **One matching project, with one real number** from the packet. Say what was built and how you knew it worked.
3. **A short ask:** a 15-minute call about [an internship, season and dates, location].
4. **A footer** with the links the packet lists (site, GitHub, resume link).

**Addresses**

- Use only addresses seen on a public page: the company's site, a founder's own site or post, or public commit metadata.
- Never guess an address pattern, and never probe mail servers (SMTP checks) to test one.
- If you can't find an address you can verify, skip the company, or use its public contact form or posted application.

**Sending**

- Write drafts only, for example as drafts in the user's mail client. The user reviews, edits and sends each one.
- Suggest weekday mornings in the recipient's time zone (Tuesday to Thursday work best).
- Follow up once after about 5 business days if there's no reply. Then stop.

**Skip a company** when the role is unpaid or mislabeled, it hires only senior people, you can't verify a hook, or its dates collide with your school terms.

**Optional, for international students:** startups often assume an international student needs costly sponsorship. A one-line P.S. ("I'd work under CPT, which my university authorizes, so the internship needs no sponsorship") can remove that doubt. The user decides whether to keep it.

**Founder email skeleton**

> Subject: [The thing from their page] and [your matching project]
>
> Hi [First name],
>
> [One sentence on the checkable hook: what you saw on their page and why it matters to you.] I built [project], which [what it does], and [one real number that shows it worked].
>
> I'm a [year] [major] student at [school], looking for a [season year] internship ([dates], [location]). Would you have 15 minutes for a call about whether I could help with [a specific problem from their page]?
>
> [Your name]
>
> [site] · [GitHub] · [resume link]

## Logging

- Every message sent, on the application it supports: `./aa set ID --note "Referral ask to [Name] (alum), template B, YYYY-MM-DD"`.
- A referral that was actually submitted: `./aa set ID --referral "Name"`. When a form asks "Referred by an employee?", the answer is then Yes, with that name.
- Founder emails: add the company with `./aa add URL --org ... --title ...` if it isn't tracked yet, then note when the draft was written, when the user sent it, and any reply.
