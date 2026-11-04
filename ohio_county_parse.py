"""Parse Ohio county board-of-elections summary reports (text from `pdftotext -layout`)
into one CSV of candidates with leaders/winners.

Handles the common ES&S / Hart / Dominion "Election Summary" layouts used by Ohio
counties. Results are UNOFFICIAL election-night counts; "winner" means the
candidate(s) leading the count (top N for a "vote for N" contest), not a call.

Usage:
  python3 ohio_county_parse.py OUT.csv COUNTY=report.pdf[@source_url] ...
(.pdf files are converted with `pdftotext -layout`; .txt files are read as-is.)
"""
import csv
import re
import subprocess
import sys

VOTE_FOR = re.compile(r"\(?\s*vote\s+for\s+(?:not\s+more\s+than\s+)?(\d+)\s*\)?", re.I)
PARTIES = r"(?:OTHER|REP|DEM|LIB|GRN|OPC|OTH|NON|IND|CON|SOC|WRITE-IN|Rep|Dem|Lib|Grn|Opc|Oth|Non|Ind)"
NUM = r"\d{1,3}(?:,\d{3})+|\d+"
SKIP = re.compile(
    r"^\s*(total|times cast|over ?votes|under ?votes|contest totals|precincts|candidate\b|choice\b|"
    r"cast votes|write-in totals|write-in:|not assigned|registered|ballots|page \d|election summary|"
    r"run (date|time)|unofficial|official|summary|statistics|jurisdiction|cumulative|reg\.|"
    r"election day|absentee|provisional|early voting|vote %|\d+ ballots)", re.I)
HEADER_NOISE = re.compile(r"(november 3, 2026|county, ohio|general election|page \d+ of|all precincts|"
                          r"election summary|summary results|unofficial|\d{1,2}/\d{1,2}/20\d\d)", re.I)


def contest_name(lines, i):
    line = lines[i]
    before = VOTE_FOR.split(line)[0].strip(" -–(")
    if len(before) > 3:
        name = before
    else:
        name = ""
        for j in range(i - 1, max(i - 4, -1), -1):
            t = lines[j].strip()
            if not t or HEADER_NOISE.search(t) or SKIP.match(t):
                if name:
                    break
                continue
            name = t
            break
    return re.sub(r"\s+", " ", name).strip()


def parse_candidate(line, sum_columns):
    s = line.strip()
    if not s or SKIP.match(s) or HEADER_NOISE.search(s):
        return None
    m = re.match(rf"^(?:({PARTIES})\s+)?(.+?)\s{{2,}}(?:({PARTIES})\s+)?((?:{NUM}).*)$", s)
    if not m:
        return None
    party = m.group(1) or m.group(3) or ""
    name = re.sub(r"\s+", " ", m.group(2)).strip()
    rest = m.group(4)
    if not re.search(r"[A-Za-z]", name) or re.fullmatch(r"[\d,.%/ ]+", name):
        return None
    if sum_columns:
        # Columns are by vote method; the last count/percent pair is the Total column.
        counts = [int(x.replace(",", "")) for x in re.findall(rf"({NUM})\s+\d+\.\d+%", rest)]
        votes = counts[-1] if counts else None
    else:
        first = re.match(rf"({NUM})", rest)
        votes = int(first.group(1).replace(",", "")) if first else None
    if votes is None:
        return None
    return {"candidate": name, "party": party.upper(), "votes": votes}


def parse(text):
    # Rejoin "(Vote for" headers that wrapped onto the next line.
    text = re.sub(r"\(Vote\s+for\s*\n\s*(\d+\))", r"(Vote for \1", text, flags=re.I)
    lines = text.splitlines()
    sum_columns = bool(re.search(r"Choice\s+Party\s+Absentee Voting", text))
    starts = [i for i, l in enumerate(lines) if VOTE_FOR.search(l)]
    contests = []
    for k, i in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        n = int(VOTE_FOR.search(lines[i]).group(1))
        cands, write_in_votes, pending = [], 0, ""
        for line in lines[i + 1:end]:
            wt = re.match(rf"^\s*Write-In Totals\s+({NUM})", line, re.I)
            if wt:
                write_in_votes += int(wt.group(1).replace(",", ""))
                continue
            # A long name can wrap: name on its own line, party/votes on the next.
            cont = re.match(rf"^\s+({PARTIES})\s+((?:{NUM}).*)$", line)
            if pending and cont:
                line = f"{pending}   {cont.group(1)}   {cont.group(2)}"
            pending = ""
            stripped = line.strip()
            if (stripped and not re.search(r"\d", stripped) and not SKIP.match(stripped)
                    and not HEADER_NOISE.search(stripped) and len(stripped.split()) >= 2):
                pending = re.sub(r"\s+", " ", stripped)
                continue
            # End of candidate list; a bare "Total" column header is not the end.
            if re.match(r"^\s*(Total Votes|Total\s+[\d,]+|Cast Votes:)", line):
                break
            c = parse_candidate(line, sum_columns)
            if c and (c["candidate"].lower().startswith(("write-in", "write in"))
                      or c["party"] == "WRITE-IN"):
                write_in_votes += c["votes"]
            elif c:
                cands.append(c)
        if not cands or all(re.match(r"(yes|no|for|against)\b", c["candidate"], re.I)
                            for c in cands):
            continue  # ballot issue, not a candidate race
        # The report's own total, to check the parse against.
        reported = None
        for line in lines[i + 1:end]:
            m = re.match(rf"^\s*(?:Total Votes(?: Cast)?|Total|Cast Votes:)\s+({NUM})\b", line)
            if m:
                nums = re.findall(rf"({NUM})\s+\d+\.\d+%", line) if sum_columns else []
                reported = int((nums[-1] if nums else m.group(1)).replace(",", ""))
                break
        contests.append({"contest": contest_name(lines, i), "vote_for": n, "candidates": cands,
                         "reported_total": reported, "write_in_votes": write_in_votes})
    return contests


def main():
    out = sys.argv[1]
    fields = ["county", "contest", "vote_for", "candidate", "party", "votes", "percent",
              "rank", "status", "contested", "total_check", "source_url"]
    rows = []
    for arg in sys.argv[2:]:
        county, rest = arg.split("=", 1)
        path, _, url = rest.partition("@")
        if path.lower().endswith(".pdf"):
            text = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True,
                                  text=True, check=True).stdout
        else:
            text = open(path, encoding="utf-8", errors="replace").read()
        for c in parse(text):
            total = sum(x["votes"] for x in c["candidates"]) or 1
            ranked = sorted(c["candidates"], key=lambda x: -x["votes"])
            contested = len(ranked) > c["vote_for"]
            # Write-ins are excluded from the candidate rows, so allow for them
            # (some reports total write-ins on a separate line we don't capture).
            rep, parsed = c["reported_total"], total + c["write_in_votes"]
            check = ("no total in report" if rep is None else
                     "ok" if 0 <= rep - parsed <= max(25, rep * 0.005) else
                     f"MISMATCH parsed {parsed} vs report {rep}")
            for r, x in enumerate(ranked, 1):
                lead = r <= c["vote_for"] and x["votes"] > 0
                status = ("unopposed" if lead and not contested else
                          "leading" if lead else "trailing")
                rows.append({"county": county, "contest": c["contest"], "vote_for": c["vote_for"],
                             "candidate": x["candidate"], "party": x["party"], "votes": x["votes"],
                             "percent": round(100 * x["votes"] / total, 2), "rank": r,
                             "status": status, "contested": contested, "total_check": check,
                             "source_url": url})
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
