"""Opportunity sources. Each module exposes fetch(src) -> list of rows:

  {id, org, title, kind, category, locations, url, posted_at, deadline, extra}

`src` is one [[sources]] table from config.toml. Ids are prefixed with the source
type so they stay stable across syncs. Add a source by writing a module with a
fetch() function and registering it in _types().
"""
import json
import re
import urllib.request

UA = {"User-Agent": "apply-anything/0.1"}


def get_json(url, timeout=30):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))


def title_filter(src):
    """Keep a title if it matches any `include` pattern (when given) and no `exclude` pattern."""
    inc = [p for p in src.get("include", []) if p]
    exc = [p for p in src.get("exclude", []) if p]
    inc_rx = re.compile("|".join(inc), re.I) if inc else None
    exc_rx = re.compile("|".join(exc), re.I) if exc else None
    return lambda t: (not inc_rx or inc_rx.search(t)) and not (exc_rx and exc_rx.search(t))


def _types():
    from . import ashby, devpost, greenhouse, lever, simplify
    return {"simplify": simplify.fetch, "greenhouse": greenhouse.fetch, "lever": lever.fetch,
            "ashby": ashby.fetch, "devpost": devpost.fetch}


def name(src):
    return src.get("name") or src["type"]


def fetch(src):
    types = _types()
    if src["type"] not in types:
        raise ValueError(f"unknown source type {src['type']!r}; known: {', '.join(types)}")
    return types[src["type"]](src)
