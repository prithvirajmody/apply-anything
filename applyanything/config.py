"""Find your profile folder and load its config.toml.

Everything personal (config, applicant packet, resume content, the database)
lives in one folder that is never committed: $AA_HOME if it is set, otherwise
./profile in the current directory, otherwise profile/ in the repo root.
"""
import copy
import os
import pathlib
import tomllib

PKG = pathlib.Path(__file__).resolve().parent
REPO = PKG.parent
EXAMPLE = REPO / "examples" / "profile"

DEFAULTS = {
    "identity": {"name": "", "email": "", "phone": "", "location": "", "links": []},
    "sources": [],
    "rank": {
        "reach": [], "competitive": [], "accessible": [],
        "fit": [], "far": [], "ineligible": [],
        "base": {"reach": 82, "competitive": 62, "solid": 42, "accessible": 24},
        # look up each Greenhouse posting's form to count required essays and cover letters
        "questions": True,
    },
    "eligibility": {
        "requires_citizenship": [],
        "needs_sponsorship": False,
        "no_sponsorship": [],
        "countries": [],
        # kinds the country filter applies to (hackathon venues rarely parse as places)
        "location_kinds": ["job", "internship"],
    },
    "batch": {
        "size": 10, "per_org": 1, "mode": "prestige", "freshness_days": 30,
        "mix": {"reach": 2, "competitive": 3, "solid": 3, "accessible": 2},
    },
    "ui": {"port": 8765},
}


def home() -> pathlib.Path:
    if os.environ.get("AA_HOME"):
        return pathlib.Path(os.environ["AA_HOME"]).expanduser()
    local = pathlib.Path.cwd() / "profile"
    return local if local.is_dir() else REPO / "profile"


def merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load(path=None) -> dict:
    p = pathlib.Path(path) if path else home() / "config.toml"
    return merge(DEFAULTS, tomllib.loads(p.read_text()) if p.exists() else {})


def db_path() -> pathlib.Path:
    return pathlib.Path(os.environ.get("AA_DB") or home() / "aa.db")
