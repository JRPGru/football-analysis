# Bundesliga 2025/26 Player Statistics Downloader

## Purpose

`data_downloader.py` is intended to build one large CSV containing season-level
statistics for every Bundesliga player in the 2025/26 season.

The goal is not to maintain separate FBref and Bundesliga.com datasets. The goal
is to create one merged player table that can later be used for analysis,
visualization, clustering, modeling, scouting-style comparisons, or database
import.

The generated CSV is:

```text
bundesliga_2025_26_all_players.csv
```

This repository/file bundle does **not** include the generated CSV. The CSV is
created only when the user runs:

```bash
python data_downloader.py
```

---

## Core source rule

The project follows a strict source priority:

1. **FBref is the primary source.**
2. If a statistic is available and populated on FBref, use the FBref value.
3. **Bundesliga.com is used only when FBref does not provide that statistic for
   2025/26.**
4. Do not duplicate a statistic from Bundesliga.com when FBref already provides
   the same concept.

This makes the final dataset as detailed as possible while keeping one preferred
source for overlapping statistics.

---

## Why two sources are needed

FBref is richer for traditional football/event and playing-time statistics.

Examples include:

- player
- team
- position
- age
- nationality
- appearances
- starts
- minutes
- 90s played
- goals
- assists
- goals per 90
- assists per 90
- shots
- shots on target
- shot accuracy
- shots per 90
- goals per shot
- cards
- fouls
- fouls drawn
- offsides
- crosses
- interceptions
- tackles won
- goalkeeper statistics
- on-pitch team-performance statistics

However, for Bundesliga 2025/26 many of FBref's old advanced tables still expose
column names but no longer contain populated data for statistics such as detailed
passing, possession, progressive actions, and some defensive metrics.

Bundesliga.com is therefore used to add physical/tracking and other league-only
statistics that FBref does not provide.

---

## FBref tables used

The downloader currently requests these player-season tables from FBref:

```text
standard
shooting
playing_time
misc
keeper
```

All distinct columns returned by these tables are kept.

The script does not manually restrict FBref to a small predefined subset of
columns. Instead, it keeps all available columns and prefixes them with their
source/table, for example:

```text
fbref_standard_...
fbref_shooting_...
fbref_playing_time_...
fbref_misc_...
fbref_keeper_...
```

This makes source provenance explicit and prevents collisions between similarly
named columns.

---

## Bundesliga.com-only statistics

The downloader currently adds these fields only because they are not available
as populated FBref player statistics for Bundesliga 2025/26:

```text
bundesliga_shots_against_post_bar
bundesliga_pass_success_open_play_pct
bundesliga_duels_won
bundesliga_aerial_duels_won
bundesliga_crosses_open_play
bundesliga_distance_km
bundesliga_top_speed_kmh
bundesliga_sprints
bundesliga_intensive_runs
```

These fields may be expanded later if Bundesliga.com exposes another useful
statistic that FBref does not contain.

---

## Important passing limitation

The desired original dataset included total completed passes.

For Bundesliga 2025/26, FBref's old detailed passing table may expose columns for
completed passes, attempts, completion percentage, and related passing metrics,
but those values are not reliably populated.

Bundesliga.com provides:

```text
Successful passes from open play (%)
```

This is a percentage, not an absolute completed-pass count.

Therefore the script currently stores the Bundesliga percentage rather than
inventing or estimating an absolute completed-pass total.

A future source may be added if a reliable freely accessible completed-passes
count is found.

---

## Player matching strategy

The two websites may spell the same player's name differently.

The script therefore:

1. keeps the original FBref player name in the final output;
2. creates a temporary normalized name;
3. removes accents and punctuation for matching;
4. first attempts exact normalized-name matches;
5. only then attempts conservative fuzzy matching;
6. accepts fuzzy matches only at a high similarity threshold and when the best
   match is clearly better than the second-best candidate;
7. leaves the value missing if the match is ambiguous.

The design principle is:

> Missing data is preferable to assigning one player's statistics to another
> player.

Unmatched Bundesliga.com names are printed after the script runs so they can be
reviewed manually.

---

## Missing values

Missing values are stored as normal pandas/CSV missing values.

The downloader does **not** replace missing statistics with zero.

This is important because:

```text
missing != zero
```

For example, absence from a leaderboard does not necessarily prove that a player
recorded zero of that statistic.

---

## Output structure

The final CSV contains one row per FBref player/team/season record.

Identifier columns are placed first:

```text
player
team
season
league
```

They are followed by:

```text
all FBref columns
all Bundesliga-only columns
```

Goalkeepers may naturally have useful keeper-specific fields that are empty for
outfield players.

Similarly, some physical rankings may have missing values for players who were
not included in the source leaderboard.

---

## Dependencies

The dependencies are also listed in `requirements.txt`. On Windows, use the
same Python interpreter for installation and running the downloader:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" -m pip install -r requirements.txt
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" -m playwright install chromium
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" data_downloader.py
```

Install the required Python packages with:

```bash
python -m pip install \
    pandas \
    numpy \
    soccerdata \
    playwright \
    rapidfuzz \
    Unidecode \
    lxml \
    html5lib
```

Playwright also needs a Chromium installation:

```bash
python -m playwright install chromium
```

---

## Running the downloader

Run:

```bash
python data_downloader.py
```

Expected output:

```text
bundesliga_2025_26_all_players.csv
```

The terminal also reports:

- number of FBref rows
- number of Bundesliga ranking entries extracted
- total output rows
- total output columns
- unmatched Bundesliga player names

---

## FBref access behavior

The script uses the `soccerdata` package for FBref.

`soccerdata` provides parsing and local caching, which is preferable to manually
hard-coding every FBref HTML table.

The downloader also spaces FBref table requests to avoid sending a rapid burst
of requests.

If the data has already been cached by `soccerdata`, subsequent runs should
generally be lighter.

---

## Bundesliga.com scraping behavior

Bundesliga.com ranking pages are dynamic.

The downloader therefore uses Playwright with headless Chromium.

For each selected ranking it:

1. opens the 2025/26 ranking page;
2. handles a cookie dialog if present;
3. repeatedly presses `Load more` where possible;
4. first tries to parse a normal HTML table;
5. falls back to a DOM-based ranking parser if necessary.

Because websites change, the Bundesliga.com parser is the part most likely to
require maintenance in the future.

The DOM parser reads the leader card and subsequent player rows using their
dedicated name/value fields. Consent handling includes the Contentpass iframe.
A disabled `Load more` button marks the end of a ranking; click failures raise
an error instead of silently accepting a partial list. Source leaderboards may
still cover fewer players than FBref.

Run the offline parser regression test (requires installed Chromium) with:

```bash
python -m unittest test_downloader
```

---

## Design principle for future changes

When adding another statistic, follow this process:

### Step 1

Check whether it is actually populated on FBref for Bundesliga 2025/26.

### Step 2

If FBref contains it, keep the FBref version.

### Step 3

If FBref does not contain it, check Bundesliga.com.

### Step 4

If Bundesliga.com contains it, add it to `BUNDESLIGA_STATS`.

### Step 5

Do not add two columns for the same statistic simply because both websites
provide it.

The intended priority remains:

```text
FBref > Bundesliga.com fallback
```

---

## Possible later improvements

Potential extensions include:

- manual name-match override dictionary;
- team-aware matching in addition to player-name matching;
- saving raw source tables for debugging;
- SQLite or DuckDB output in addition to CSV;
- automatic schema summary;
- per-90 derived metrics for Bundesliga physical data;
- validation of player counts and team counts;
- data-quality report for unmatched or missing fields;
- support for additional seasons;
- additional reliable data source for absolute completed passes.

---

## Current project scope

Current intended scope:

```text
Competition: Bundesliga
Season:      2025/26
Granularity: one row per player/team season record
Primary:     FBref
Fallback:    Bundesliga.com
Output:      CSV
```

Do not silently expand the script to other leagues or seasons unless that is
explicitly requested.
