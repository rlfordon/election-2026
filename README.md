# election-2026

Tools and data for finding projected/called winners of the **November 3, 2026** US general election, so they can be compared against an alumni list.

## What's here

| Path | What it is |
|---|---|
| `civicapi_winners.py` | Pulls every Nov 3, 2026 US race from [civicAPI](https://civicapi.org) and writes the two CSVs below. |
| `data/winners_2026.csv` | Candidates civicAPI has **called as winners** (~3,500 rows). |
| `data/candidates_2026.csv` | **Every candidate** in every candidate race (~87,000 rows), with a call status. |

The committed CSVs are a snapshot taken around **1 pm ET on Nov 4, 2026**. Re-run the script for fresher data:

```bash
python3 civicapi_winners.py data
```

It needs only the Python 3 standard library, with no API key. A full pull fetches about 39,500 races and takes a few minutes.

### CSV columns

`candidate, party, status, votes, percent, race_type, election_name, state, district, municipality, percent_reporting, race_called, race_id, race_url`

`status` is one of:

- `WON (called)`: civicAPI has called the race for this candidate
- `lost (called)`: the race is called for someone else
- `leading (not called)`: the race isn't called yet and this candidate has the most votes so far
- `not called`: the race isn't called yet and this candidate isn't leading

`race_url` returns the race's full detail from civicAPI, including county-level breakdowns and `called_at`.

### What civicAPI covers

Called-race counts as of the snapshot:

| Office | Races | Called |
|---|---|---|
| US Senate | 36 | 33 |
| US House | 436 | 377 |
| Governor | 40 | 34 |
| AG / Secretary of State / Lt. Gov | 68 | 42 |
| State Senate | 1,184 | 678 |
| State House | 4,574 | 2,257 |
| Local (mayor, council, school board, judges, county offices, etc.) | ~30,000 | almost none |

### Caveats

- **The calls are civicAPI's own projections, not AP's or any network's.** civicAPI doesn't publish how it makes them, and they haven't been checked against AP.
- **Local races have vote counts but essentially no calls.** For these, `leading (not called)` is the most you'll get.
- **Some races are left out of the CSVs:** referendums, and about 90 state-legislative or national rows that only report totals by party.
- **Name matching:** civicAPI keeps middle initials and nicknames (e.g. `Jonathan S. "JKT" Kreiss-Tomkins`). Match on fuzzy name + state rather than exact name.
- **Blocked user agent:** civicAPI blocks Python's default user agent, so the script sends its own.
- **Attribution required:** civicAPI's terms require crediting **civicapi.org** in anything shared beyond personal use.

## Getting other races

### AP Elections API (paid, includes race calls)

This is the authoritative source for race calls, but it needs a licensed AP key (`api.ap.org` is reachable from this environment; it answers `403` without a key). To use it, add the key in the cloud environment settings as **`AP_API_KEY`** under Network secrets (or as an environment variable), then start a new session. Don't paste keys into chat.

### Open America (free, no calls)

`https://openamerica.io/elections/results.json?year=2026&office=House|Senate|Governor`

This is a free feed of House, Senate and Governor vote counts from official state election offices. It needs no key and has no quota.

- It covers **22 states** only.
- It makes **no race calls**. Its `leader` field just shows who's ahead in the count.
- Attribution: "official state election offices via Open America (openamerica.io)", shown with the feed's `as_of` timestamp.

### State and county election offices (official)

These are the most authoritative source, and for most **local, county and trial-court judicial races** they're the only one. Formats vary: some offices publish JSON (e.g. Virginia Dept. of Elections, LA County), but most publish PDF summary reports. Nobody "calls" these races; the winner is whoever leads the certified count.

### Ohio specifically

civicAPI has only **162 Ohio races**: federal, statewide, General Assembly, Ohio Supreme Court and Courts of Appeals. Known gaps as of the snapshot:

- **Court of Appeals:** all 22 races show 0% reporting, so this data looks stale.
- **Supreme Court:** both races show 100% reporting but are uncalled.
- **Other statewide offices:** SoS, AG, Treasurer and Auditor all show 100% reporting with the leader near 50.5%, and none is called.
- **Not covered at all:** county offices (commissioner, auditor, prosecutor, sheriff), Common Pleas, probate, juvenile and municipal judges, and city or township races.

For those, use:

1. **Ohio Secretary of State** ([ohiosos.gov](https://www.ohiosos.gov/elections/election-results-and-data/)) for official statewide, congressional, legislative and appellate/Supreme Court results. It probably doesn't cover county offices or trial-court judges (not confirmed). The site is behind Cloudflare and blocks automated requests from this environment, so open it in a browser.
2. **County boards of elections (88 counties)** for county offices and Common Pleas, probate, juvenile and municipal judges. Most boards post an *Election Summary Report* PDF, and the format is fairly consistent across counties.

   **`data/ohio/county_results_directory.csv`** lists every county's results page, taken from the Secretary of State's [Local Election Results directory](https://www.ohiosos.gov/directories/local-election-results) (saved from a browser on Nov 4, 2026). It also records whether the page loads from this cloud environment:
   - **Reachable (23):** Butler, Clermont, Crawford, Cuyahoga, Delaware, Franklin, Guernsey, Hancock, Henry, Lake, Lorain, Mahoning, Mercer, Morrow, Ottawa, Sandusky, Stark, Trumbull, Union, Warren, Wayne, Williams, Wood.
   - **Blocked (65):** the 57 counties on the shared `boe.ohio.gov` host (including Summit), plus Allen, Columbiana, Coshocton, Hamilton, Huron, Lucas, Montgomery and Portage. Download these in a browser.

   Examples:
   - [Stark](https://www.starkcountyohio.gov/Board%20of%20Elections/Election%20Results/2026/General/ElectionSummaryReportRPT_Unofficial.pdf?t=202611032331260)
   - [Trumbull](https://boe.co.trumbull.oh.gov/pdfs/Election%20Summary.pdf)
   - [Lorain](https://www.boe.ohio.gov/lorain/c/elecres/20261103results.pdf)
   - [Ashtabula](https://www.boe.ohio.gov/ashtabula/c/elecres/20261103results.pdf)
   - [Geauga](https://www.boe.ohio.gov/geauga/c/elecres/20261103precinct.pdf)
   - Cuyahoga: [boe.cuyahogacounty.gov](https://boe.cuyahogacounty.gov/)
   - Franklin: [vote.franklincountyohio.gov](https://vote.franklincountyohio.gov/)
   - Hamilton: [votehamiltoncountyohio.gov](https://votehamiltoncountyohio.gov/)

   For a blocked county, download the PDF in a browser and add it to the repo (e.g. `data/ohio/<county>.pdf`) so it can be parsed.
3. **Local news** can help cross-check judge races, but treat it as secondary. Examples: Signal Cleveland (Cuyahoga judges), Dayton Daily News (Montgomery), WOUB (Tuscarawas).

All county results are **unofficial** until the official canvass is finished in late November. Provisional and late-arriving absentee ballots are still being counted.

## Suggested workflow for the alumni comparison

1. Add the alum list as a CSV in the repo, with name, state, and county/court if known. Don't paste it into chat.
2. Match it against `data/candidates_2026.csv` on fuzzy name + state.
3. For alumni in local or judicial races not in civicAPI, especially in Ohio, pull those counties' summary PDFs and parse them.
4. Re-check close or uncalled races after certification.
