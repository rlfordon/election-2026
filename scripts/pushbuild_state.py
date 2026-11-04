"""Pull one state's 2026 results from pushbuild/us-2026-election-results (CC0) and
summarize statewide leaders.

Pushbuild reads each state's official results feed (for Ohio, the Secretary of
State's). Counts are unofficial; "leading" is the top vote-getter, not a call.

Usage: python3 scripts/pushbuild_state.py [STATE] [out_dir]   (default: OH data/ohio)
Writes:
  <st>_sos_feed_2026.csv      the pushbuild file as published (statewide + county rows)
  <st>_state_races_2026.csv   statewide candidate rows with rank and leading/trailing/unopposed
"""
import csv
import io
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

RAW = "https://raw.githubusercontent.com/pushbuild/us-2026-election-results/main/data/{}.csv"
UA = {"User-Agent": "election-2026-research/0.1"}


def main():
    st = (sys.argv[1] if len(sys.argv) > 1 else "OH").lower()
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "data/ohio")
    out.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(RAW.format(st), headers=UA)
    text = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
    (out / f"{st}_sos_feed_2026.csv").write_text(text)

    contests = defaultdict(list)
    for r in csv.DictReader(io.StringIO(text)):
        if r["level"] == "state":
            contests[r["contest"]].append(r)
    fields = ["contest", "candidate", "party", "votes", "pct", "rank", "status",
              "precincts_reporting", "precincts_total", "source", "fetched_at"]
    rows = []
    for contest, cands in contests.items():
        ranked = sorted(cands, key=lambda r: -int(r["votes"] or 0))
        opposed = len(ranked) > 1
        for i, r in enumerate(ranked, 1):
            status = ("unopposed" if not opposed else "leading" if i == 1 else "trailing")
            rows.append({"contest": contest, "candidate": r["candidate"], "party": r["party"],
                         "votes": r["votes"], "pct": r["pct"], "rank": i, "status": status,
                         "precincts_reporting": r["precinctsReporting"],
                         "precincts_total": r["precinctsTotal"], "source": r["source"],
                         "fetched_at": r["fetchedAt"]})
    with open(out / f"{st}_state_races_2026.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{st.upper()}: {len(contests)} statewide contests, {len(rows)} rows -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
