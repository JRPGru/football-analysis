# AGENTS.md

## Project Overview

This repository is a personal football data-analysis and visualization project.

The current workflow is:

```text
FBref
  │
  ▼
data_downloader.py
  │
  ▼
data/<league>/data_<season>_all_players.csv
  │
  ▼
prepare_pca.py
  │
  ├── configurable PCA analysis
  ├── PCA player coordinates
  ├── PCA loadings
  ├── PCA summary
  └── Viz/data_sources.json
          │
          ▼
      Viz/
          │
          ▼
Interactive 3D Plotly visualization
```

The project supports multiple leagues and multiple seasons.

Do not make the code Bundesliga-specific unless explicitly requested.

---

# General Development Rules

## Preserve the current architecture

Do not reintroduce old project components that are no longer used.

In particular, the current project:

- uses **FBref** as the football-statistics source
- uses `soccerdata` for FBref access
- supports arbitrary configured leagues and seasons
- does **not** use Bundesliga.com
- does **not** use Playwright
- does **not** use RapidFuzz for cross-site player matching
- does **not** merge statistics from multiple websites

If a new external source is desired, it must be explicitly requested.

---

## Code responses

When code changes are requested:

- provide the **complete updated file**
- do not provide only a diff unless explicitly requested
- put the complete file in one copyable code block
- do not create downloadable files unless explicitly requested
- keep the existing project structure unless a structural change is necessary
- explain important behavioral changes briefly before or after the code

For README updates, return the entire README in **one single Markdown code block** so it can be copied directly.

---

# Project Structure

The intended structure is approximately:

```text
Football Analysis/
│
├── data/
│   │
│   ├── bundesliga/
│   │   ├── data_2025_26_all_players.csv
│   │   └── ...
│   │
│   ├── premier_league/
│   │   ├── data_2025_26_all_players.csv
│   │   └── ...
│   │
│   └── ...
│
├── Viz/
│   ├── index.html
│   ├── styles.css
│   ├── visualization.js
│   └── data_sources.json
│
├── data_downloader.py
├── prepare_pca.py
├── requirements.txt
├── .gitignore
├── README.md
└── AGENTS.md
```

League directories are generated from the league name.

Examples:

```text
GER-Bundesliga
→ data/bundesliga/

ENG-Premier League
→ data/premier_league/

ESP-La Liga
→ data/la_liga/
```

---

# data_downloader.py

## Purpose

`data_downloader.py` downloads FBref player-season statistics for a specified league and season.

Typical usage:

```powershell
python data_downloader.py --league "GER-Bundesliga" --season "2025-2026"
```

or:

```powershell
python data_downloader.py --league "ENG-Premier League" --season "2025-2026"
```

Do not hardcode one particular league or season.

---

## FBref source

The downloader currently uses the following FBref player-season tables:

```text
standard
shooting
playing_time
misc
keeper
```

FBref columns are flattened into stable source-aware names.

Examples:

```text
fbref_standard_playing_time_min
fbref_shooting_standard_sh_per_90
fbref_playing_time_team_success_plus_minus90
fbref_misc_performance_int
fbref_keeper_performance_saves
```

Preserve these source-aware names.

They are intentionally verbose because they allow a metric to be selected unambiguously later in `prepare_pca.py`.

---

## Missing values

Missing source data must remain missing.

Do not automatically replace missing statistics with zero.

The semantic rule is:

```text
missing != zero
```

---

## Excluded columns

The following FBref miscellaneous columns are currently excluded because they have been empty/unusable in the downloaded datasets:

```text
fbref_misc_performance_pkwon
fbref_misc_performance_pkcon
```

Do not reintroduce them without verifying that they contain meaningful data.

---

## Output

A download for:

```text
GER-Bundesliga
2025-2026
```

should produce:

```text
data/bundesliga/data_2025_26_all_players.csv
```

A Premier League download for the same season should produce:

```text
data/premier_league/data_2025_26_all_players.csv
```

The downloaded source CSVs are intended to remain in the repository.

---

# prepare_pca.py

## Purpose

`prepare_pca.py` transforms a downloaded league/season dataset into three configurable PCA dimensions.

Typical usage:

```powershell
python prepare_pca.py --league "GER-Bundesliga" --season "2025-2026"
```

The same league and season identifiers used by `data_downloader.py` should be used here.

---

# PCA Configuration

The most important design principle of `prepare_pca.py` is that the PCA definition should be editable from a clear configuration block near the top of the file.

The exact FBref CSV column names should be selected there.

Conceptually:

```python
PCA_GROUPS = [

    {
        "name": "Shooting",

        "metrics": [
            "fbref_standard_per_90_minutes_gls",
            "fbref_shooting_standard_sh_per_90",
            "fbref_shooting_standard_sot_per_90",
        ],
    },

    {
        "name": "Team Success",

        "metrics": [
            "fbref_playing_time_team_success_ppm",
            "fbref_playing_time_team_success_plus_minus90",
            "fbref_playing_time_team_success_on_off",
        ],
    },

    {
        "name": "General Activity",

        "metrics": [
            "fbref_misc_performance_fls",
            "fbref_misc_performance_fld",
            "fbref_misc_performance_int",
        ],
    },

]
```

The configuration should be easy to modify without changing PCA implementation code.

---

## PCA group order

The group order defines the plot axes:

```text
PCA_GROUPS[0] → PC1 → X
PCA_GROUPS[1] → PC2 → Y
PCA_GROUPS[2] → PC3 → Z
```

Exactly three groups are currently required because the visualization is three-dimensional.

---

## PCA group names

Each PCA group has a human-readable:

```python
"name"
```

That name is not cosmetic only.

It must propagate through the output pipeline and be used by the visualization.

For example:

```python
{
    "name": "Chance Creation",
    ...
}
```

should cause the corresponding plot axis to display:

```text
Chance Creation
```

Do not hardcode PCA axis meanings in `visualization.js`.

---

## Metric names

Metrics should be selected using their exact FBref CSV column names.

For example:

```python
"fbref_shooting_standard_sh_per_90"
```

Do not create unnecessary intermediate names such as:

```text
shots_per90
shooting_metric_1
offensive_score_input
```

when the actual FBref column name can be used directly.

The goal is for a user to be able to look at the FBref glossary or downloaded CSV and copy the desired metric name directly into `PCA_GROUPS`.

---

# Metric Semantics

Do not silently change the meaning of a selected metric.

If the user selects a total/count column, it remains a count.

If the user selects a per-90 column, it remains per 90.

If the user selects a percentage, it remains a percentage.

If the user selects a ratio, it remains a ratio.

Do not automatically derive a per-90 version from every count.

---

# Player Aggregation

The raw FBref dataset can contain multiple rows for one player if the player represented multiple teams during the season.

`prepare_pca.py` should combine those rows into one player before PCA.

Total minutes are summed across rows.

Players are retained only if they have:

```python
minutes > MIN_MINUTES
```

The default threshold is:

```python
MIN_MINUTES = 400
```

This means exactly 400 minutes is excluded.

---

## Metadata aggregation

For players with multiple team rows:

- combine all represented teams for display/filtering
- use the row with the most minutes for primary metadata such as position and age

Position is metadata only.

Position must never be included automatically as a PCA feature.

---

## Statistical aggregation

When multiple team rows need to be combined:

### Additive statistics

Counts/totals can be summed where appropriate.

Examples include concepts such as:

```text
goals
shots
fouls
interceptions
cards
```

### Non-additive statistics

Rates, percentages, averages, ratios, and similar statistics should not simply be summed.

When appropriate, use playing-time-weighted aggregation.

Examples include:

```text
per-90 values
percentages
PPM
On-Off
ratios
```

Be careful when adding new metric types.

Do not guess that a statistic is additive simply because it is numeric.

---

# PCA Preprocessing

Each PCA group should be handled independently.

The intended process is:

```text
selected metrics
      │
      ▼
remove completely empty features
      │
      ▼
median imputation
      │
      ▼
remove zero-variance features
      │
      ▼
standardization
      │
      ▼
PCA(n_components=1)
      │
      ▼
standardized PCA score
```

---

## Missing values

Completely empty selected metrics should be reported and removed rather than causing the entire run to fail unnecessarily.

For remaining features:

```text
missing values → median imputation
```

The output should retain information about how many metrics were:

```text
observed
imputed
```

for each player and PCA group.

---

## Standardization

All PCA inputs must be standardized before PCA.

This is essential because the selected FBref metrics can have very different scales and units.

The PCA components themselves should also be standardized after calculation so that:

```text
mean ≈ 0
standard deviation ≈ 1
```

for each PCA axis.

---

# PCA Direction

Remember that PCA sign is mathematically arbitrary.

Changing every score and loading from:

```text
+x
```

to:

```text
-x
```

describes the same PCA solution.

Do not interpret the default PCA sign as automatically meaning:

```text
positive = good
negative = bad
```

unless explicit orientation logic has been configured.

If future work adds user-defined metric desirability such as:

```python
direction = +1
direction = -1
```

prefer using it to orient the final PCA axis rather than changing the underlying PCA input values.

Do not convert PCA into a weighted player rating unless explicitly requested.

---

# PCA Output

For:

```text
GER-Bundesliga
2025-2026
```

the expected generated analysis files are:

```text
data/bundesliga/player_pca_fbref_2025_26.csv
data/bundesliga/pca_loadings_fbref_2025_26.csv
data/bundesliga/pca_summary_fbref_2025_26.csv
```

---

## Player PCA file

The player PCA output should include at least:

```text
league
season
player
team
position
position_group
age
minutes
PC1
PC2
PC3
PC1_label
PC2_label
PC3_label
```

It should also include:

- selected FBref metrics
- observed-feature counts
- imputed-feature counts

---

## PCA loadings

The loadings CSV should make it possible to inspect what each component represents.

Useful fields include:

```text
axis
group_name
metric
loading
used_in_pca
drop_reason
observed_pct
imputation_median
explained_variance_pct
```

Do not hide dropped features.

A feature excluded because it is all missing or zero variance should be visible in the output with an appropriate reason.

---

## PCA summary

The PCA summary should contain one row per PCA group and include information such as:

```text
axis
name
feature_count_requested
feature_count_used
explained_variance_pct
metrics
```

---

# Visualization Manifest

`prepare_pca.py` is also responsible for generating:

```text
Viz/data_sources.json
```

It should scan prepared PCA datasets below:

```text
data/
```

and expose the available league/season combinations to the frontend.

Each source should contain information similar to:

```json
{
    "id": "bundesliga-2025_26",
    "league": "GER-Bundesliga",
    "league_name": "Bundesliga",
    "season": "2025-2026",
    "season_label": "2025/26",
    "axis_labels": {
        "PC1": "Shooting",
        "PC2": "Team Success",
        "PC3": "General Activity"
    },
    "path": "../data/bundesliga/player_pca_fbref_2025_26.csv"
}
```

Axis labels must come from the current PCA configuration.

Do not hardcode them in the manifest builder.

---

# Viz/

The visualization consists of:

```text
Viz/index.html
Viz/styles.css
Viz/visualization.js
Viz/data_sources.json
```

It uses Plotly for the 3D player plot.

---

## Dataset selection

The visualization has separate selectors for:

```text
League
Season
```

The available seasons depend on the selected league.

When the selected dataset changes, the visualization should rebuild:

- player data
- club list
- available ages
- player count
- axis labels

Do not retain stale filters from the previously selected dataset.

---

# Dynamic PCA Axis Names

The visualization must not contain fixed assumptions such as:

```javascript
"Shooting profile (PC1)"
"Team success (PC2)"
"Misc performance (PC3)"
```

Axis labels must come from the dataset metadata.

Primary source:

```javascript
CURRENT_SOURCE.axis_labels
```

For example:

```javascript
CURRENT_SOURCE.axis_labels.PC1
CURRENT_SOURCE.axis_labels.PC2
CURRENT_SOURCE.axis_labels.PC3
```

The generated player CSV may also contain:

```text
PC1_label
PC2_label
PC3_label
```

These can be used as a fallback.

If no configured label is available, fall back to:

```text
PC1
PC2
PC3
```

---

## Dynamic page text

The selected PCA group names should also be used where appropriate in:

- plot axis titles
- page subtitle
- hover information

Changing only the names inside `PCA_GROUPS` followed by rerunning `prepare_pca.py` should be enough to update the visible PCA names.

The user should not need to edit `visualization.js` every time a PCA group is renamed.

---

# Plot Behavior

The current visualization uses four position traces:

```text
GK
DF
MF
FW
```

Position colours:

```text
GK → orange
DF → yellow
MF → green
FW → blue
```

Inactive/filter-mismatched players remain visible in gray.

Filters should not remove them from the chart.

---

## Filters

Current filters:

```text
position
club
minimum age
maximum age
```

Within one category, multiple choices use OR logic.

Different filter categories combine using AND logic.

Example:

```text
(MF OR FW)
AND
(Arsenal OR Liverpool)
AND
(age <= 25)
```

---

# Plotly Camera

Current desired behavior:

- `scatter3d`
- turntable rotation
- scroll zoom
- orthographic projection
- Z axis stays visually upward
- Cartesian grid remains visible
- large filled background planes are disabled

Do not revert to perspective projection unless explicitly requested.

---

# Local Visualization

The frontend should be served through HTTP.

From the project root:

```powershell
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/Viz/
```

Do not instruct the user to open:

```text
file:///.../Viz/index.html
```

because browser file-access restrictions can prevent the manifest and CSV files from loading correctly.

---

# Git / Generated Files

The repository should track:

```text
data/
data/<league>/
data/<league>/data_<season>_all_players.csv
```

In other words:

- downloaded source datasets are tracked
- league directories are represented through their source datasets

The CSV files generated by PCA analysis should **not** be stored in Git.

Current generated PCA patterns:

```gitignore
data/**/player_pca_fbref_*.csv
data/**/pca_loadings_fbref_*.csv
data/**/pca_summary_fbref_*.csv
```

Legacy PCA filenames should also remain ignored:

```gitignore
data/**/player_pca_fbref.csv
data/**/pca_loadings_fbref.csv
data/**/pca_summary_fbref.csv
```

Do not add a rule such as:

```gitignore
data/
```

because the downloaded source datasets should remain tracked.

---

## Important deployment implication

The visualization loads prepared PCA CSV files.

If PCA output CSVs are ignored by Git, GitHub Pages cannot load them from the repository unless the deployment workflow generates or copies them during deployment.

Keep this distinction in mind when changing deployment behavior.

Do not silently change the `.gitignore` policy to solve deployment problems.

---

# README Rules

When updating `README.md`:

- describe the current implementation only
- remove descriptions of deprecated architectures
- keep it concise enough to function as a GitHub README
- include setup
- include downloader usage
- include PCA configuration
- include visualization launch instructions
- include multi-league / multi-season behavior
- explain that PCA axis names are configurable
- return the entire README in one copyable Markdown code block

The Author section should end with:

```text
Nur der HSV!
```

For example:

```markdown
## Author

Developed by **Jossy Grundmann**.

Personal project for football data collection, configurable dimensionality reduction, and interactive player-profile visualization.

**Nur der HSV!**
```

---

# Source Fidelity

When modifying data-processing logic:

- use the actual column names present in the downloaded CSV
- do not invent statistics that are not present
- do not infer missing values as zero
- do not silently substitute a similar FBref metric for a requested one
- do not change units without making the transformation explicit
- do not describe a count as per 90 unless it actually is per 90
- do not describe a percentage as an absolute count
- do not silently change the meaning of a selected PCA metric

If a requested metric does not exist in the source CSV, fail clearly and report the exact missing column.

---

# Design Priorities

When making changes, prioritize:

1. **Correct data semantics**
2. **Transparent metric selection**
3. **Configurable PCA definitions**
4. **Reproducibility**
5. **Multi-league and multi-season support**
6. **Simple visualization workflow**
7. **Readable code**
8. **Minimal hardcoding**

Avoid adding complexity that does not directly support one of these goals.

---

# Current Scope

The current project can be summarized as:

```text
Source:          FBref
Downloader:      soccerdata
Leagues:         configurable
Seasons:         configurable
Raw storage:     league-specific CSV
PCA groups:      3 configurable groups
PCA metrics:     exact FBref CSV columns
PCA axis names:  configurable
Visualization:   interactive 3D Plotly
Filters:         position, club, age
Dataset select:  league + season
Deployment:      static frontend / GitHub Pages compatible architecture
```

Do not silently reintroduce assumptions from older versions of the project.