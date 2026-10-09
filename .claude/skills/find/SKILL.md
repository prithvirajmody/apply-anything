---
name: find
description: Find opportunities beyond the configured feeds (hackathons, fellowships, scholarships, grants, accelerators, research programs, conferences, events, or roles at specific kinds of companies) with web search, check each one is real, open and fits the user's profile, and add it to the tracker. Use when the user runs /find or asks to find things to apply to.
---

# /find <what>

Example: `/find ML fellowships for undergrads`, `/find hackathons in the Bay Area this month`,
`/find robotics startups hiring summer interns`.

1. Read `profile/packet.md` sections 3–5 (education, work authorization, standard answers)
   and `profile/config.toml` [eligibility], so you only add things the user can apply to.
2. Search the web. Prefer the organizer's own page over aggregators. For each candidate,
   open the official page and confirm:
   - it's open (deadline in the future, or rolling) and the dates work for the user;
   - eligibility (year in school, degree, citizenship or residency, location, age) fits the packet;
   - how to apply (form, platform, account needed) and what it asks for (essays, letters,
     references, transcript, video).
3. Add each one that passes:
   `./aa add <official url> --org "<org>" --title "<name>" --kind <hackathon|fellowship|scholarship|grant|program|event|internship|job> --deadline <YYYY-MM-DD> --note "<what it asks for; why it fits>"`.
   Check `./aa list --q "<org>" --all` first so nothing is added twice.
4. Report a short table: name, kind, deadline, what it asks for, why it fits, plus the ones
   you rejected and why. Suggest `./aa batch --mode deadline` when several have close deadlines.

Never add something you couldn't verify on an official page. Never sign up, register or
apply as part of /find; that's `/apply`, with the user's OK.
