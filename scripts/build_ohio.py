"""Build ohio_candidates_2026.csv: every candidate in Ohio's Nov 3, 2026 races that
we have results for, in one file.

- State-level races (statewide, Supreme Court, Courts of Appeals, Congress,
  General Assembly): Ohio Secretary of State results feed, via
  pushbuild/us-2026-election-results (CC0).
- County-level races (county offices, Common Pleas judges, etc.): each county
  board of elections' unofficial summary report (PDF), parsed with
  ohio_county_parse.py. Only counties listed in COUNTY_REPORTS are included.

Counts are unofficial. Nobody calls these races: status is leading / trailing /
unopposed (top N of a "vote for N" race leads).

Usage: python3 scripts/build_ohio.py [out.csv]   (default: ohio_candidates_2026.csv)
Needs pdftotext (poppler-utils).
"""
import csv
import io
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ohio_county_parse import parse  # noqa: E402

UA = {"User-Agent": "election-2026-research/0.1"}
PUSHBUILD_OH = "https://raw.githubusercontent.com/pushbuild/us-2026-election-results/main/data/oh.csv"

# county, report URL, report run time (as printed on the report)
COUNTY_REPORTS = [
    ("Clermont", "https://boe.clermontcountyohio.gov/168of168.pdf?t=202611032305450", "2026-11-03 10:47 PM"),
    ("Crawford", "https://crawfordcountyohioboe.gov/wp-content/uploads/Unoffical-Election-Summary-11-3-2026.pdf", "2026-11-03 11:07 PM"),
    ("Cuyahoga", "https://boe.cuyahogacounty.gov/docs/default-source/boe/elections/unofficial-results-by-contest6cf43809237341b488fad00c6228e1bf.pdf?sfvrsn=9f877902_1", "2026-11-04 5:29 AM"),
    ("Guernsey", "https://boe.guernseycounty.gov/wp-content/uploads/2026/11/Guernsey-Co.-November-3-2026-Unofficial-General-Election-Summary-Report-All-35-Precincts-incl.-Absentee-and-Early-Voting.pdf", "2026-11-03 9:47 PM"),
    ("Ottawa", "https://boe.ottawa.oh.gov/wp-content/uploads/2026/11/electionsummary9pm.pdf", "2026-11-03 8:58 PM"),
    ("Sandusky", "https://sanduskycountyoh.gov/uploads/board%20of%20elections/2026/Sandusky%20County%20Unofficial%20Results%20(2).PDF", "2026-11-03 8:49 PM"),
    ("Stark", "https://www.starkcountyohio.gov/Board%20of%20Elections/Election%20Results/2026/General/ElectionSummaryReportRPT_WI.pdf", "2026-11-04 11:07 AM"),
    ("Trumbull", "https://boe.co.trumbull.oh.gov/pdfs/Election%20Summary.pdf", "2026-11-04 6:37 AM"),
    ("Wayne", "https://www.waynecountyoh.gov/wp-content/uploads/2026/11/Unofficial-Canvass-Incl-WI-Gen-26.pdf", "2026-11-04 11:43 AM"),
    ("Williams", "https://www.williamscountyoh.gov/DocumentCenter/View/4052/Unofficial-Cumulative-Results-1132026", "2026-11-03 9:24 PM"),
    ("Wood", "https://boe.woodcountyohio.gov/DocumentCenter/View/1028/Unofficial-Results", "2026-11-03 11:15 PM"),
]

# Races covered by the state feed; drop them from county reports to avoid duplicates.
STATE_LEVEL = re.compile(
    r"senat|governor|congress|attorney general|auditor of state|secretary of state|"
    r"treasurer of state|state of ohio|supreme court|sup crt|appeals|state rep|"
    r"representative to|u\.s\.|united states|issue", re.I)

PARTY = {"D": "Democratic", "DEM": "Democratic", "R": "Republican", "REP": "Republican",
         "L": "Libertarian", "LIB": "Libertarian", "G": "Green", "GRN": "Green",
         "NO": "Nonpartisan", "NP": "Nonpartisan", "NON": "Nonpartisan",
         "OPC": "Other", "OP": "Other", "OTH": "Other", "OTHER": "Other", "XX": ""}

FIELDS = ["candidate", "party", "status", "votes", "percent", "race", "county",
          "as_of", "source", "source_url"]


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()


def ranked_rows(race, county, cands, seats, as_of, source, url):
    total = sum(c["votes"] for c in cands) or 1
    ranked = sorted(cands, key=lambda c: -c["votes"])
    for i, c in enumerate(ranked, 1):
        if len(ranked) <= seats:
            status = "unopposed"
        else:
            status = "leading" if i <= seats and c["votes"] > 0 else "trailing"
        yield {"candidate": c["candidate"], "party": PARTY.get(c["party"].upper(), c["party"]),
               "status": status, "votes": c["votes"], "percent": round(100 * c["votes"] / total, 2),
               "race": race, "county": county, "as_of": as_of, "source": source, "source_url": url}


def state_level():
    races = {}
    for r in csv.DictReader(io.StringIO(get(PUSHBUILD_OH).decode("utf-8"))):
        if r["level"] != "state" or r["party"] == "WI" or "Issue" in r["contest"]:
            continue  # county breakdowns, write-ins, ballot issues
        races.setdefault(r["contest"], []).append(
            {"candidate": r["candidate"], "party": r["party"], "votes": int(r["votes"] or 0),
             "as_of": r["fetchedAt"]})
    for race, cands in races.items():
        yield from ranked_rows(race, "", cands, 1, cands[0]["as_of"][:16].replace("T", " ") + " UTC",
                               "Ohio Secretary of State (via Pushbuild)",
                               "https://github.com/pushbuild/us-2026-election-results")


def county_level():
    with tempfile.TemporaryDirectory() as tmp:
        for county, url, as_of in COUNTY_REPORTS:
            pdf = Path(tmp) / f"{county}.pdf"
            pdf.write_bytes(get(url))
            text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                                  capture_output=True, text=True, check=True).stdout
            for c in parse(text):
                if STATE_LEVEL.search(c["contest"]):
                    continue
                yield from ranked_rows(c["contest"], county, c["candidates"], c["vote_for"],
                                       as_of, f"{county} County Board of Elections", url)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "ohio_candidates_2026.csv")
    rows = list(state_level()) + list(county_level())
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
