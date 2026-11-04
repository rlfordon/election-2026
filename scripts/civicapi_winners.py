"""Export 2026 general-election candidates and calls from civicAPI (civicapi.org) to CSV.

Calls are civicAPI's own projections, not AP's. Attribution to civicapi.org is
required for non-personal projects.

Usage: python3 scripts/civicapi_winners.py [out_dir]   (default: data/civicapi)
Writes:
  candidates_2026.csv  every candidate in every candidate-level race, with status
  winners_2026.csv     only candidates civicAPI has called as winners
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
ELECTION_DATE = "2026-11-03"
PAGE = 500


def fetch_all():
    races, offset = [], 0
    while True:
        url = (f"{API}?startDate={ELECTION_DATE}&endDate={ELECTION_DATE}"
               f"&country=US&limit={PAGE}&offset={offset}")
        req = urllib.request.Request(url, headers=UA)
        page = json.load(urllib.request.urlopen(req, timeout=60))["races"]
        if not page:
            return races
        races += page
        offset += len(page)
        print(f"fetched {offset} races", file=sys.stderr)
        time.sleep(0.5)


def norm(name):
    return re.sub(r"\s+", " ", name or "").strip()


def is_party_rollup(race):
    # Some legislative/national rows aggregate by party ("Republican", "Democrats").
    return race["province"] == "US" or all(
        c["name"] == c["party"] or c["name"] in ("Democrats", "Republicans")
        for c in race["candidates"])


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "data/civicapi")
    out.mkdir(parents=True, exist_ok=True)
    races = fetch_all()
    fields = ["candidate", "party", "status", "votes", "percent", "race_type",
              "election_name", "state", "district", "municipality",
              "percent_reporting", "race_called", "race_id", "race_url"]
    rows = []
    for r in races:
        if r["type"] == "Referendum" or is_party_rollup(r):
            continue
        called = any(c.get("winner") for c in r["candidates"])
        top = max(r["candidates"], key=lambda c: c.get("votes") or 0, default=None)
        for c in r["candidates"]:
            if c.get("winner"):
                status = "WON (called)"
            elif called:
                status = "lost (called)"
            elif top is c and (c.get("votes") or 0) > 0:
                status = "leading (not called)"
            else:
                status = "not called"
            rows.append({
                "candidate": norm(c["name"]), "party": c.get("party"),
                "status": status, "votes": c.get("votes"), "percent": c.get("percent"),
                "race_type": r["type"], "election_name": r["election_name"],
                "state": r["province"], "district": r.get("district"),
                "municipality": r.get("municipality"),
                "percent_reporting": r.get("percent_reporting"),
                "race_called": called, "race_id": r["id"],
                "race_url": f"https://civicapi.org/api/v2/race/{r['id']}",
            })
    for name, subset in (("candidates_2026.csv", rows),
                         ("winners_2026.csv", [x for x in rows if x["status"] == "WON (called)"])):
        with open(out / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(subset)
        print(f"wrote {out / name}: {len(subset)} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
