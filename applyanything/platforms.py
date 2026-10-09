"""Recognize the application platform behind a URL and who has to do what on it.

filler:
  agent    a form the agent can fill end to end with no account
  account  you create an account or sign in first, then the agent fills it
  check    the organization's own portal: open it once to see what it needs
"""

# URL fragment -> platform, for forms that need no account
NO_ACCOUNT = {
    "greenhouse": "Greenhouse", "grnh.se": "Greenhouse", "gh_jid=": "Greenhouse", "lever.co": "Lever",
    "ashbyhq": "Ashby", "smartrecruiters": "SmartRecruiters", "jobvite": "Jobvite", "workable": "Workable",
    "rippling": "Rippling", "bamboohr": "BambooHR", "applytojob": "JazzHR", "pinpointhq": "Pinpoint",
    "paylocity": "Paylocity", "careerpuck": "CareerPuck", "dover.com": "Dover", "lu.ma": "Luma",
    "luma.com": "Luma", "typeform.com": "Typeform", "docs.google.com/forms": "Google Forms",
    "forms.gle": "Google Forms", "tally.so": "Tally", "airtable.com": "Airtable", "jotform": "Jotform",
    "fillout.com": "Fillout",
}
# URL fragment -> platform, for portals that need an account or a sign-in code
ACCOUNT = {
    "myworkdayjobs": "Workday", "myworkdaysite": "Workday", "icims": "iCIMS", "oraclecloud": "Oracle",
    "successfactors": "SuccessFactors", "taleo": "Taleo", "eightfold": "Eightfold", "avature": "Avature",
    "yello.co": "Yello", "amazon.jobs": "Amazon", "google.com/about/careers": "Google",
    "careers.google.com": "Google", "lifeattiktok": "TikTok", "bytedance": "ByteDance", "brassring": "BrassRing",
    "ultipro": "UKG", "adp.com": "ADP", "phenompeople": "Phenom", "devpost.com": "Devpost",
    "partiful.com": "Partiful", "cerebralvalley.ai": "Cerebral Valley", "handshake": "Handshake",
}
ACCOUNT_NOTE = {
    "Workday": "Workday: one account per company (email, password, verify), then the agent fills the wizard",
    "Oracle": "Oracle: you enter the one-time email code, then the agent fills the steps",
    "Amazon": "Amazon: sign in to amazon.jobs; an online assessment often follows right after applying",
    "Google": "Google: sign in with your Google account; may ask for a transcript",
    "Devpost": "Devpost: register with your Devpost account; the project submission itself is yours",
    "Partiful": "Partiful: signs in with a code texted to your phone",
}


def detect(url):
    """Return (platform, filler, note) for an application URL."""
    u = (url or "").lower()
    for k, name in NO_ACCOUNT.items():
        if k in u:
            return name, "agent", "no account needed: the agent can fill all of it"
    for k, name in ACCOUNT.items():
        if k in u:
            return name, "account", ACCOUNT_NOTE.get(name, f"{name}: you create the account or sign in, then the agent fills it")
    return "", "check", "own portal: open it once to see what the form needs"
