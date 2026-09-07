# Football Player Analysis

Interactive football player profiling based on FBref statistics and configurable grouped PCA.

The project downloads player statistics for a selected league and season, groups selected FBref metrics into three PCA dimensions, and visualizes the resulting player profiles in an interactive 3D Plotly plot.

The PCA metrics and axis names are configured directly at the top of `prepare_pca.py`, so the analysis can be changed without modifying the visualization code.

---

## Features

- Player statistics downloaded directly from **FBref**
- Support for multiple leagues and seasons
- Configurable PCA metric groups
- Custom names for all three PCA axes
- Automatic handling of players who changed clubs
- Minimum playing-time threshold
- Median imputation of missing PCA values
- Standardization before PCA
- PCA loading and explained-variance output
- Interactive 3D Plotly visualization
- League and season selection
- Position, club, and age filtering
- Dynamic PCA axis labels
- Position-based player colours
- Player information on hover
- Static frontend suitable for GitHub Pages

---

## Project Workflow

```text
FBref
  │
  ▼
data_downloader.py
  │
  ▼
Raw league/season CSV
  │
  ▼
prepare_pca.py
  │
  ├── Player PCA data
  ├── PCA loadings
  ├── PCA summary
  └── Viz/data_sources.json
          │
          ▼
      Visualization
```

---

# 1. Download Data

Player-season statistics are downloaded from FBref using `soccerdata`.

The league and season are selected from the command line.

### Bundesliga

```powershell
python data_downloader.py --league "GER-Bundesliga" --season "2025-2026"
```

### Premier League

```powershell
python data_downloader.py --league "ENG-Premier League" --season "2025-2026"
```

The resulting files are stored automatically in league-specific directories:

```text
data/
├── bundesliga/
│   └── data_2025_26_all_players.csv
│
└── premier_league/
    └── data_2025_26_all_players.csv
```

The downloader currently combines the following FBref player tables:

- `standard`
- `shooting`
- `playing_time`
- `misc`
- `keeper`

FBref columns are flattened while preserving their source table, for example:

```text
fbref_standard_playing_time_min
fbref_shooting_standard_sh_per_90
fbref_playing_time_team_success_plus_minus90
fbref_misc_performance_int
fbref_keeper_performance_saves
```

Missing FBref values remain missing and are not automatically interpreted as zero.

Players who changed clubs can occur in multiple rows in the raw dataset.

---

# 2. Configure the PCA

The PCA definition is located at the top of:

```text
prepare_pca.py
```

There are exactly three PCA groups:

```python
PCA_GROUPS = [

    {
        "name": "Shooting",

        "metrics": [
            "fbref_standard_per_90_minutes_gls",
            "fbref_shooting_standard_sh_per_90",
            "fbref_shooting_standard_sot_per_90",
            "fbref_shooting_standard_sotpct",
            "fbref_shooting_standard_g_per_sh",
            "fbref_shooting_standard_g_per_sot",
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
            "fbref_misc_performance_off",
            "fbref_misc_performance_crs",
            "fbref_misc_performance_int",
            "fbref_misc_performance_tklw",
        ],
    },

]
```

The order of the groups determines the visualization axes:

```text
PCA_GROUPS[0] → PC1 → X axis
PCA_GROUPS[1] → PC2 → Y axis
PCA_GROUPS[2] → PC3 → Z axis
```

The `name` field defines the human-readable axis name.

For example:

```python
{
    "name": "Defensive Activity",
    "metrics": [
        ...
    ],
}
```

will automatically produce an axis named:

```text
Defensive Activity
```

in the visualization.

The visualization therefore does not need to be edited whenever the PCA groups are renamed.

---

## Selecting Metrics

Metrics are selected using their **exact column names from the downloaded FBref CSV**.

For example:

```python
"fbref_shooting_standard_sh_per_90"
```

selects FBref's shots-per-90 metric directly.

The PCA preparation does not silently convert every selected metric into another form.

This means that selecting:

```text
fbref_misc_performance_fls
```

uses the total fouls metric, while selecting an existing per-90 column uses that per-90 metric.

The exact variable names can be taken from the downloaded CSV or the FBref column glossary.

---

# 3. PCA Preprocessing

Run PCA preparation using the same league and season used during downloading.

### Bundesliga

```powershell
python prepare_pca.py --league "GER-Bundesliga" --season "2025-2026"
```

### Premier League

```powershell
python prepare_pca.py --league "ENG-Premier League" --season "2025-2026"
```

The script performs the following preprocessing.

### Player aggregation

Players who represented multiple clubs during the season are combined into one player.

Playing time is summed across club rows.

For selected statistics:

- additive totals are summed
- rates, ratios, percentages, and similar non-additive metrics are combined using playing-time-weighted averages

The player's main position and age are taken from the row in which the player accumulated the most minutes.

All represented clubs are retained for filtering in the visualization.

### Playing-time filter

Only players with **strictly more than 400 minutes** are included by default.

The threshold is configured in:

```python
MIN_MINUTES = 400
```

### Missing values

For each PCA group:

1. Completely empty metrics are removed.
2. Remaining missing values are median-imputed.
3. Zero-variance metrics are removed.

The output records how many selected metrics were observed and imputed for each player.

### Standardization

All metrics are standardized before PCA:

```text
mean = 0
standard deviation = 1
```

This prevents variables with larger numerical scales from dominating the PCA solely because of their units.

### PCA

Each metric group receives its own independent one-component PCA.

The three resulting components form:

```text
PC1
PC2
PC3
```

The final PCA scores are also standardized to mean 0 and standard deviation 1.

Player position is **not used as an input to PCA**.

It is used only for colouring and filtering players in the visualization.

---

# PCA Output

For Bundesliga 2025/26, preprocessing creates:

```text
data/bundesliga/
├── player_pca_fbref_2025_26.csv
├── pca_loadings_fbref_2025_26.csv
└── pca_summary_fbref_2025_26.csv
```

## Player PCA file

```text
player_pca_fbref_2025_26.csv
```

contains:

- league
- season
- player
- team
- position
- age
- minutes
- PC1
- PC2
- PC3
- PCA axis labels
- selected FBref metrics
- observed/imputed metric counts

The PCA axis names are also stored as:

```text
PC1_label
PC2_label
PC3_label
```

---

## PCA Loadings

```text
pca_loadings_fbref_2025_26.csv
```

contains the contribution of each selected metric to its PCA component.

It also records whether a feature was actually used or had to be removed because it was:

- completely missing
- zero variance

This file can be used to interpret what each PCA axis represents statistically.

---

## PCA Summary

```text
pca_summary_fbref_2025_26.csv
```

contains information including:

- PCA axis
- configured axis name
- number of requested metrics
- number of metrics actually used
- explained variance
- selected metric list

---

# 4. Dataset Manifest

After every PCA run, `prepare_pca.py` scans the prepared datasets below:

```text
data/
```

and regenerates:

```text
Viz/data_sources.json
```

The manifest contains information about each prepared league/season combination, including:

```json
{
    "league": "GER-Bundesliga",
    "season": "2025-2026",
    "axis_labels": {
        "PC1": "Shooting",
        "PC2": "Team Success",
        "PC3": "General Activity"
    }
}
```

The visualization uses this file to determine:

- available leagues
- available seasons
- PCA CSV location
- PCA axis names

This allows the frontend to remain static while supporting multiple datasets.

---

# 5. Visualization

The frontend is located in:

```text
Viz/
├── index.html
├── styles.css
├── visualization.js
└── data_sources.json
```

Each eligible player is displayed as a point in a rotatable 3D Plotly scatter plot.

The coordinates are:

```text
X → PC1
Y → PC2
Z → PC3
```

The visible names of these axes come directly from the PCA configuration in `prepare_pca.py`.

For example:

```python
"name": "Chance Creation"
```

will automatically appear as:

```text
Chance Creation
```

on the corresponding plot axis.

The same names are also used in the page subtitle and player hover information.

---

## Dataset Selection

The visualization provides separate selectors for:

- **League**
- **Season**

Changing the league automatically updates the seasons available for that league.

Changing either selector reloads the corresponding PCA dataset.

The following are rebuilt for the selected dataset:

- club list
- age range
- player count
- PCA axis names
- plotted players

---

## Filters

Players can be filtered by:

- position
- club
- minimum age
- maximum age

Filters within one category use OR logic.

Different filter categories are combined using AND logic.

For example:

```text
Position = MF OR FW
AND
Club = Arsenal
AND
Age <= 25
```

Unmatched players are not removed from the plot.

Instead, they remain visible in gray.

---

## Position Colours

| Position | Colour |
|----------|--------|
| GK | Orange |
| DF | Yellow |
| MF | Green |
| FW | Blue |

Position is used only for visualization and filtering.

---

# 6. Adding More Data

## Add another league

For example, Premier League 2025/26:

```powershell
python data_downloader.py --league "ENG-Premier League" --season "2025-2026"
python prepare_pca.py --league "ENG-Premier League" --season "2025-2026"
```

The Premier League will then appear automatically in the league selector.

---

## Add another season

For example, Bundesliga 2024/25:

```powershell
python data_downloader.py --league "GER-Bundesliga" --season "2024-2025"
python prepare_pca.py --league "GER-Bundesliga" --season "2024-2025"
```

Bundesliga will then have both seasons available:

```text
2025/26
2024/25
```

Each league only displays seasons for which a prepared PCA dataset exists.

---

# 7. Installation

Install the required Python packages from the project directory:

```powershell
python -m pip install -r requirements.txt
```

The current downloader is FBref-only and does not require Playwright or Bundesliga.com scraping.

---

# 8. Running the Visualization Locally

Start the HTTP server from the **project root**:

```powershell
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/Viz/
```

For example, the terminal should be located at:

```text
Football Analysis/
```

and not inside:

```text
Football Analysis/Viz/
```

because the visualization also needs access to the files under:

```text
data/
```

Do not open `Viz/index.html` directly using `file://`.

The visualization loads both `data_sources.json` and the PCA CSV files through HTTP.

If the browser still displays an older JavaScript or CSS version after an update, perform a hard refresh:

```text
Ctrl + Shift + R
```

---

# Example Workflow

Download Bundesliga:

```powershell
python data_downloader.py --league "GER-Bundesliga" --season "2025-2026"
```

Prepare Bundesliga:

```powershell
python prepare_pca.py --league "GER-Bundesliga" --season "2025-2026"
```

Download Premier League:

```powershell
python data_downloader.py --league "ENG-Premier League" --season "2025-2026"
```

Prepare Premier League:

```powershell
python prepare_pca.py --league "ENG-Premier League" --season "2025-2026"
```

Start the local server:

```powershell
python -m http.server 8000
```

Open:

```text
http://localhost:8000/Viz/
```

The league selector will now contain both prepared leagues.

---

# Project Structure

```text
Football Analysis/
│
├── data/
│   │
│   ├── bundesliga/
│   │   ├── data_2025_26_all_players.csv
│   │   ├── player_pca_fbref_2025_26.csv
│   │   ├── pca_loadings_fbref_2025_26.csv
│   │   └── pca_summary_fbref_2025_26.csv
│   │
│   ├── premier_league/
│   │   ├── data_2025_26_all_players.csv
│   │   ├── player_pca_fbref_2025_26.csv
│   │   ├── pca_loadings_fbref_2025_26.csv
│   │   └── pca_summary_fbref_2025_26.csv
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
└── README.md
```

---

# Author

Developed by **Jossy Grundmann**.

Personal project for football data collection, configurable dimensionality reduction, and interactive player-profile visualization. - Nur der HSV!