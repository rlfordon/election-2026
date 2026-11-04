# 2026 US general election: candidates and winners

Candidate-level results for the **November 3, 2026** general election. There's one file for the whole US and one for Ohio, which goes deeper.

| File | What's in it |
|---|---|
| `us_candidates_2026.csv` | Every candidate in about 36,800 races nationwide, from US Senate down to local offices, with race calls where they exist |
| `ohio_candidates_2026.csv` | Every Ohio state-level race, plus county offices and Common Pleas judges for 11 counties |

**All counts are unofficial.** States certify results in late November and December.

## Columns

Both files start with the same five columns:

| Column | Meaning |
|---|---|
| `candidate` | Name as published |
| `party` | Party |
| `status` | One of the values listed below |
| `votes` | Votes so far |
| `percent` | Share of the race's votes |

**Status values:**

- `won` / `lost`: the race has been called (US file only)
- `leading` / `trailing`: the race isn't called; leading means currently ahead. In races electing more than one person ("vote for 3"), the top 3 are `leading`.
- `unopposed`: the only candidate

**Other columns:**

- **US file:** `office` (e.g. `US Senate`, `State House`, `Mayor`), `race`, `state`, `district`, `municipality`, `percent_reporting`, `as_of`, `source_url`
- **Ohio file:** `race`, `county` (blank for state-level races), `as_of`, `source`, `source_url`

## How complete is it?

### US file

**Source:** [civicAPI](https://civicapi.org). The race calls are civicAPI's own, not AP's or a network's.

**Snapshot:** 2:54 pm ET, Nov 4, 2026.

**Judicial retention votes** (e.g. `Kelli M. Evans Retention`) appear with `Yes` and `No` as the candidates. The judge's name is in `race`. Ballot measures are left out.

| Office | Races | Called |
|---|---|---|
| US Senate | 35 | 33 |
| US House | 435 | 382 |
| Governor | 39 | 34 |
| State Senate | 1,142 | 678 |
| State House | 4,528 | 2,257 |
| Local offices | ~30,000 | almost none |

For uncalled races, use `leading`.

### Ohio file

Nobody calls these races, so every status is `leading`, `trailing` or `unopposed`.

**State-level races** (322 rows): U.S. Senate, Congress, Governor and the other statewide offices, Ohio Supreme Court, the Courts of Appeals, and the General Assembly.
- **Source:** the Ohio Secretary of State, via [Pushbuild](https://github.com/pushbuild/us-2026-election-results).
- **Snapshot:** 12:15 pm ET, Nov 4, with all precincts reporting.

**County-level races** (94 rows): county commissioner, auditor and other county offices, Common Pleas judges (general, probate, juvenile, domestic relations), and a few local races.
- **Source:** each county board of elections' unofficial report.
- **Counties included:** Clermont, Crawford, Cuyahoga, Guernsey, Ottawa, Sandusky, Stark, Trumbull, Wayne, Williams, Wood.
- **Missing:** the other 77 counties, including Franklin, Hamilton, Summit, Montgomery and Lucas. Their reports either weren't posted yet or are on sites that block automated download.

## Other states

For state and county-level results from official state feeds in 40 states, see [pushbuild/us-2026-election-results](https://github.com/pushbuild/us-2026-election-results). It has one CSV per state. Coverage varies: some states include every county, some only statewide totals.

## Updating

```bash
python3 scripts/build_us.py      # US file (a few minutes)
python3 scripts/build_ohio.py    # Ohio file (needs pdftotext / poppler-utils)
```

To add an Ohio county, add its summary-report URL to `COUNTY_REPORTS` in `scripts/build_ohio.py`.

## Credits

- **US file:** [civicAPI](https://civicapi.org). Attribution is required for non-personal use.
- **Ohio state-level races:** Ohio Secretary of State, via [Pushbuild](https://github.com/pushbuild/us-2026-election-results) (CC0).
- **Ohio county races:** each county's board of elections. The report URL is in `source_url`.
