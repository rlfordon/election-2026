# election-2026

Candidate-level results and projected winners for the **November 3, 2026** US general election, plus the scripts that build them.

- **National:** every race tracked by [civicAPI](https://civicapi.org), with civicAPI's race calls.
- **Ohio:** county-level races (county offices, Common Pleas/probate/juvenile judges, municipal and township races) parsed from county board-of-elections reports.

All results are **unofficial** election-night counts. Certified results come after the official canvass (late November 2026).

## Layout

```
data/
  civicapi/
    candidates_2026.csv           every candidate in every candidate race, with call status
    winners_2026.csv              candidates civicAPI has called as winners
  ohio/
    county_results_2026.csv       candidates and leaders from parsed county reports
    county_report_status_2026.csv which report was used for each county, or why none was
    county_results_directory.csv  results page for all 88 Ohio counties
    reports/                      the source county PDFs
scripts/
  civicapi_winners.py             builds data/civicapi/
  ohio_county_parse.py            builds data/ohio/county_results_2026.csv from county PDFs
```

## National data (civicAPI)

**Snapshot:** about 1 pm ET, Nov 4, 2026. That pull covered 39,481 races.

**Columns in `data/civicapi/candidates_2026.csv`:**

| Column | Description |
|---|---|
| `candidate`, `party` | Candidate name (whitespace normalized) and party |
| `status` | `WON (called)`, `lost (called)`, `leading (not called)`, or `not called` |
| `votes`, `percent` | Current count |
| `race_type`, `election_name` | Office, e.g. `US Senate`, `State House`, `Judicial` |
| `state`, `district`, `municipality` | Location |
| `percent_reporting`, `race_called` | Race progress |
| `race_id`, `race_url` | civicAPI race id; the URL returns full detail, including county breakdowns and `called_at` |

`winners_2026.csv` has the same columns, filtered to `WON (called)`.

**Calls at snapshot time:**

| Office | Races | Called |
|---|---|---|
| US Senate | 36 | 33 |
| US House | 436 | 377 |
| Governor | 40 | 34 |
| AG / Secretary of State / Lt. Gov | 68 | 42 |
| State Senate | 1,184 | 678 |
| State House | 4,574 | 2,257 |
| Local (mayor, council, school board, judges, county offices, etc.) | ~30,000 | almost none |

**Notes:**

- **Calls are civicAPI's own projections**, not AP's or any network's. civicAPI doesn't publish its methodology.
- **Local races have vote counts but almost no calls.**
- **Excluded:** referendums, and about 90 state-legislative or national rows that only report totals by party.
- **Names** keep middle initials and nicknames as published (e.g. `Jonathan S. "JKT" Kreiss-Tomkins`).

**Refresh** (Python 3 standard library only, no API key, takes a few minutes):

```bash
python3 scripts/civicapi_winners.py            # writes data/civicapi/
```

## Ohio county data

**What civicAPI covers in Ohio:** 162 races. That's federal, statewide, General Assembly, Ohio Supreme Court and Courts of Appeals. At snapshot time:

- The Court of Appeals races showed 0% reporting.
- The SoS, AG, Treasurer and Auditor races were uncalled at 100% reporting.

**What civicAPI doesn't cover:** county offices, trial-court judges and local races. Those are only published by the 88 county boards of elections, so this repo parses those boards' summary reports.

### `data/ohio/county_results_2026.csv`

**Coverage:** 11 counties (Clermont, Crawford, Cuyahoga, Guernsey, Ottawa, Sandusky, Stark, Trumbull, Wayne, Williams, Wood). That's 442 candidate rows across about 220 races. Ballot issues are excluded.

**Columns:**

| Column | Description |
|---|---|
| `county`, `contest`, `vote_for` | Contest as printed in the report, and the number of seats |
| `candidate`, `party`, `votes`, `percent` | Write-ins are excluded |
| `rank`, `status` | `leading` (top N for a "vote for N" contest), `trailing`, or `unopposed`. Counties don't call races. |
| `contested` | Whether there are more candidates than seats |
| `total_check` | Parsed votes compared with the report's own contest total. Every contest is `ok`; Wood's report prints no totals (`no total in report`). |
| `source_url` | The report the row came from (copy in `reports/`) |

**Notes:**

- Governor/Lt. Governor ticket names that wrap in the PDFs can be truncated (e.g. `Vivek Ramaswamy and`). Use the civicAPI data for statewide races.
- Report run times and precinct counts are in `county_report_status_2026.csv`.
- Ottawa's and Sandusky's reports are early-evening runs. Later versions may exist.

### Counties not yet included

`county_report_status_2026.csv` covers the 23 counties whose sites allow automated access:

| Reason | Counties |
|---|---|
| Report found but not parsed | Mercer (scanned image), Union (precinct-level report only) |
| Results only on `liveresults.boe.ohio.gov`, which blocks automated access | Butler, Warren |
| Report hosted on `boe.ohio.gov`, which blocks automated access | Lorain |
| No Nov 3 summary report found when checked | Delaware, Franklin, Hancock, Henry, Lake, Mahoning, Morrow |

The other **65 counties** block automated access. These are the 57 counties on the shared `boe.ohio.gov` host (including Summit), plus Allen, Columbiana, Coshocton, Hamilton, Huron, Lucas, Montgomery and Portage. `county_results_directory.csv` lists every county's results page, taken from the Ohio Secretary of State's [Local Election Results directory](https://www.ohiosos.gov/directories/local-election-results).

### Adding a county

1. Download the county's *Election Summary* PDF from its results page (see `county_results_directory.csv`) into `data/ohio/reports/`.
2. Re-run the parser, listing every county to include. The output file is rewritten.

   ```bash
   python3 scripts/ohio_county_parse.py data/ohio/county_results_2026.csv \
     Clermont=data/ohio/reports/Clermont-2026-11-03-unofficial.pdf@<source url> \
     Hamilton=data/ohio/reports/Hamilton-2026-11-03-unofficial.pdf@<source url> ...
   ```

3. Check `total_check` for the new county.

The parser needs `pdftotext` (poppler-utils). It handles the common ES&S, Hart and Dominion summary layouts used by Ohio counties.

## Other sources

| Source | Cost | Calls? | Notes |
|---|---|---|---|
| AP Elections API | Paid (licensed key) | Yes | The standard source for race calls |
| [pushbuild/us-2026-election-results](https://github.com/pushbuild/us-2026-election-results) | Free, CC0 | No | Statewide and county-level CSVs read from official state feeds for about 40 states. Its Ohio file comes from the Secretary of State's feed: the same 162 state-level races as civicAPI, including Court of Appeals vote counts, but no county offices or trial-court judges |
| [openelections/openelections-data-oh](https://github.com/openelections/openelections-data-oh) | Free | No | Historical Ohio results (through 2020); useful for prior-cycle comparisons |
| [Open America](https://openamerica.io/elections/api/) | Free, no key | No | House, Senate and Governor counts from official state feeds; 22 states. `results.json?year=2026&office=House\|Senate\|Governor` |
| [Ohio Secretary of State](https://www.ohiosos.gov/elections/election-results-and-data/) | Free | No | Official statewide, congressional, legislative and appellate results |
| State and county election offices | Free | No | The only source for most local and trial-court races. Mostly PDFs; some publish JSON (e.g. Virginia, LA County) |

## Attribution

- **civicAPI** data requires attribution to [civicapi.org](https://civicapi.org) for non-personal use.
- **Ohio county results** come from each county's board of elections. Source URLs are in the data.
