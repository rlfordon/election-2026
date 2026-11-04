"""Build us_candidates_2026.csv: every candidate in every Nov 3, 2026 US race that
civicAPI (civicapi.org) tracks, with civicAPI's race calls.

status:
  won / lost             civicAPI has called the race
  leading / trailing     not called yet; leading = most votes so far
  unopposed              not called; only one candidate

Calls are civicAPI's own projections, not AP's. Attribution to civicapi.org is
required for non-personal use. Ballot measures and party-total-only rows are
skipped. Judicial retention votes are kept: candidate is Yes/No, judge is in `race`.

Usage: python3 scripts/build_us.py [out.csv]   (default: us_candidates_2026.csv)
"""
import csv
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

API = "https://civicapi.org/api/v2/race/search"
UA = {"User-Agent": "election-2026-research/0.1"}  # civicAPI blocks Python's default UA
FIELDS = ["candidate", "party", "status", "votes", "percent", "office", "race", "state",
          "district", "municipality", "percent_reporting", "as_of", "source_url"]


def fetch_all():
    races, offset = [], 0
    while True:
        url = f"{API}?startDate=2026-11-03&endDate=2026-11-03&country=US&limit=500&offset={offset}"
        req = urllib.request.Request(url, headers=UA)
        page = json.load(urllib.request.urlopen(req, timeout=60))["races"]
        if not page:
            return races
        races += page
        offset += len(page)
        print(f"fetched {offset} races", file=sys.stderr)
        time.sleep(0.5)


def is_party_rollup(race):
    return race["province"] == "US" or all(
        c["name"] == c["party"] or c["name"] in ("Democrats", "Republicans")
        for c in race["candidates"])


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "us_candidates_2026.csv")
    as_of = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    rows = []
    for r in fetch_all():
        cands = r["candidates"]
        yes_no = all(re.match(r"(yes|no|for|against)\b", c["name"] or "", re.I) for c in cands)
        # Skip ballot measures; keep judicial retention votes (judge named in `race`).
        if (r["type"] == "Referendum" or is_party_rollup(r)
                or (yes_no and "retention" not in r["election_name"].lower())):
            continue
        called = any(c.get("winner") for c in cands)
        top = max(cands, key=lambda c: c.get("votes") or 0, default=None)
        for c in cands:
            if called:
                status = "won" if c.get("winner") else "lost"
            elif len(cands) == 1:
                status = "unopposed"
            elif c is top and (c.get("votes") or 0) > 0:
                status = "leading"
            else:
                status = "trailing"
            rows.append({
                "candidate": re.sub(r"\s+", " ", c["name"] or "").strip(),
                "party": c.get("party"), "status": status, "votes": c.get("votes"),
                "percent": c.get("percent"), "office": r["type"], "race": r["election_name"],
                "state": r["province"], "district": r.get("district"),
                "municipality": r.get("municipality"),
                "percent_reporting": r.get("percent_reporting"), "as_of": as_of,
                "source_url": f"https://civicapi.org/api/v2/race/{r['id']}",
            })
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
