# Oracle Recruiting Cloud (Candidate Experience)

No account. You apply with an email address.

## Recognize it

- `<pod>.fa.<region>.oraclecloud.com/hcmUI/CandidateExperience/<lang>/sites/<site>/job/<id>` (a company domain may redirect here)
- The apply flow continues under `.../job/<id>/apply/...`

## Flow

1. Screen with the REST API (below).
2. Apply → enter the email. The same page asks you to accept terms; that's the user's.
3. If the site already knows the email, it may send a one-time code to confirm identity. Find it and show it to the user; the user enters it.
4. Fill the application: contact details, questions, resume, and any extra sections the site configured.
5. Hand off. The user submits.

## Field quirks

- Each site configures its own sections and order. Read each section's DOM before filling it.
- Few quirks are recorded yet. Add them here as you meet them.

## Leave for the user

- The terms acceptance, and the e-signature block (a typed full name) if the site has one.
- Emailed codes.
- EEO questions unless the packet answers them, and Submit.

## Screening API

One requisition. `<site>` is the `sites/<site>` part of the job URL; the quotes are URL-encoded as `%22`.

```bash
curl -s 'https://<host>/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?onlyData=true&expand=all&finder=ById;Id=%22<id>%22,siteNumber=<site>'
```

`items[0]` has `Title`, `ExternalDescriptionStr`, `ExternalQualificationsStr`, `ExternalResponsibilitiesStr`, `PrimaryLocation` and `secondaryLocations`.

Search a site:

```bash
curl -s 'https://<host>/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList&finder=findReqs;siteNumber=<site>,limit=25'
```

`items[0].requisitionList[]` lists each job's `Id`, `Title`, `PrimaryLocation` and `PostedDate`.
