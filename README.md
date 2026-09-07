# Football Player Analysis

Interactive football player profiling based on FBref statistics and grouped PCA.

The project downloads player data for a selected league and season, transforms the statistics into three interpretable player-profile dimensions, and visualizes the resulting players in an interactive 3D Plotly plot.

## Features

- Download player statistics directly from **FBref**
- Support for multiple leagues and seasons
- Automatic player aggregation after transfers
- Minimum playing-time threshold of **more than 400 minutes**
- Three independent PCA-based player dimensions
- Interactive 3D player visualization
- League and season selection
- Position, club, and age filters
- Position-based player colours
- Detailed player statistics on hover
- Static frontend suitable for GitHub Pages

## Workflow

The project consists of three main steps:

```text
FBref
  │
  ▼
data_downloader.py
  │
  ▼
Raw player statistics
  │
  ▼
prepare_pca.py
  │
  ├── PCA player data
  ├── PCA loadings
  ├── PCA summary
  └── Viz/data_sources.json
          │
          ▼
      Visualization
```

## 1. Download Data

Player-season statistics are downloaded from FBref using `soccerdata`.

Example for the Bundesliga:

```powershell
python data_downloader.py --league "GER-Bundesliga" --season "2025-2026"
```

Example for the Premier League:

```powershell
python data_downloader.py --league "ENG-Premier League" --season "2025-2026"
```

The data is stored automatically in league-specific directories:

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

FBref columns are flattened while preserving the source table, for example:

```text
fbref_standard_playing_time_min
fbref_shooting_standard_sh
fbref_playing_time_team_success_plus_minus
fbref_misc_performance_int
fbref_keeper_performance_saves
```

Missing values remain missing and are not interpreted as zero.

Players who changed clubs can appear in multiple rows in the raw data because each row represents a player/team/season combination.

## 2. Prepare PCA Data

Run the PCA preprocessing using the same league and season:

```powershell
python prepare_pca.py --league "GER-Bundesliga" --season "2025-2026"
```

The preprocessing:

- combines multiple team rows belonging to the same player
- sums playing time across those rows
- keeps players with **more than 400 minutes**
- creates per-90 and ratio-based metrics
- median-imputes missing PCA values
- removes unusable zero-variance features
- standardizes all PCA features
- calculates one principal component for each feature group
- standardizes the resulting PCA scores

Player **position is not used as a PCA feature**. It is only retained for visualization and filtering.

### PC1 — Shooting

Represents the player's shooting profile using:

- goals per 90
- shots per 90
- shots on target per 90
- shots on target percentage
- goals per shot
- goals per shot on target
- penalties scored per 90
- penalty attempts per 90

### PC2 — Team Success

Represents team performance while the player is on the pitch using:

- points per match
- team goals for per 90
- team goals against per 90
- plus/minus per 90
- on-off per 90

### PC3 — Miscellaneous Performance

Represents a broader activity profile using:

- yellow cards per 90
- red cards per 90
- second yellow cards per 90
- fouls committed per 90
- fouls drawn per 90
- offsides per 90
- crosses per 90
- interceptions per 90
- tackles won per 90
- own goals per 90

The exact contribution of each metric can be inspected in the generated PCA loadings file.

## PCA Output

For Bundesliga 2025/26:

```text
data/bundesliga/
├── player_pca_fbref_2025_26.csv
├── pca_loadings_fbref_2025_26.csv
└── pca_summary_fbref_2025_26.csv
```

The files contain:

- `player_pca_fbref_YYYY_YY.csv` — visualization-ready player data and PCA coordinates
- `pca_loadings_fbref_YYYY_YY.csv` — feature contribution to each PCA axis
- `pca_summary_fbref_YYYY_YY.csv` — PCA summary and explained variance

The visualization coordinates are stored as:

```text
PC1
PC2
PC3
```

## 3. Visualization

The frontend is located in:

```text
Viz/
├── index.html
├── styles.css
├── visualization.js
└── data_sources.json
```

`prepare_pca.py` scans the prepared PCA datasets under `data/` and updates:

```text
Viz/data_sources.json
```

This manifest is used by the static browser visualization to determine which datasets are available.

The visualization provides separate selectors for:

- **League**
- **Season**

Changing the selected league updates the available seasons.

Changing either league or season reloads the corresponding PCA dataset and automatically rebuilds the available:

- clubs
- positions
- age range
- player count

### Position Colours

| Position | Colour |
|----------|--------|
| GK | Orange |
| DF | Yellow |
| MF | Green |
| FW | Blue |

Filters do not remove unmatched players from the plot.

Instead, unmatched players remain visible in gray while matching players retain their position colour.

## Running the Visualization Locally

Start a local HTTP server from the **project root**:

```powershell
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/Viz/
```

Do not open `Viz/index.html` directly using `file://`, because the visualization needs HTTP access to load the dataset manifest and PCA CSV files.

If the browser still displays an older JavaScript or CSS version after changes, perform a hard refresh:

```text
Ctrl + Shift + R
```

## Adding Another League

For example, to add the Premier League:

```powershell
python data_downloader.py --league "ENG-Premier League" --season "2025-2026"
python prepare_pca.py --league "ENG-Premier League" --season "2025-2026"
```

Reload the visualization and **Premier League** will appear in the league selector.

## Adding Another Season

For example:

```powershell
python data_downloader.py --league "GER-Bundesliga" --season "2024-2025"
python prepare_pca.py --league "GER-Bundesliga" --season "2024-2025"
```

The new season will then appear under Bundesliga in the season selector.

## Project Structure

```text
Football Analysis/
│
├── data/
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

## Installation

Install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

The current downloader is FBref-only and does not require Playwright or Bundesliga.com scraping.

## Example Workflow

Download and prepare Bundesliga:

```powershell
python data_downloader.py --league "GER-Bundesliga" --season "2025-2026"
python prepare_pca.py --league "GER-Bundesliga" --season "2025-2026"
```

Download and prepare Premier League:

```powershell
python data_downloader.py --league "ENG-Premier League" --season "2025-2026"
python prepare_pca.py --league "ENG-Premier League" --season "2025-2026"
```

Start the visualization:

```powershell
python -m http.server 8000
```

Open:

```text
http://localhost:8000/Viz/
```

Both prepared leagues will then be available through the league selector.

## Author

Developed by **Jossy Grundmann**.

Personal project for football data collection, dimensionality reduction, and interactive player-profile visualization.