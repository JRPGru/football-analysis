# Football Analysis

A personal project for exploring and visualizing Bundesliga player statistics.

## Overview

The project currently has two main parts:

1. **Data collection**  
   `data_downloader.py` combines Bundesliga 2025/26 player-season statistics into
   `bundesliga_2025_26_all_players.csv`.

2. **3D player-profile visualization**  
   `prepare_pca.py` transforms the raw player statistics into three interpretable
   PCA-based profile dimensions and writes `player_pca.csv`, which is visualized
   interactively in the browser with Plotly.

The three visualization axes are:

- **Physical intensity**
- **Offensive activity**
- **Defensive activity**

Player position is **not** used to calculate the PCA scores. It is only used for
colouring and filtering the points.

## Data sources

FBref is the primary source. Bundesliga.com adds physical and other statistics
that are unavailable from FBref.

The downloader keeps missing values as missing and reports ambiguous player-name
matches rather than guessing.

Each row in the raw CSV represents a player/team/season record. Players who
changed clubs can therefore occur more than once in the raw data.

See [CSV glossary (German)](CSV_GLOSSAR_DE.md) for explanations of all CSV
columns, abbreviations, units, examples, and interpretation notes.

## PCA preprocessing

`prepare_pca.py` combines player rows and keeps players with more than **400
Bundesliga minutes**.

It then creates three independent one-component PCA scores.

### Physical intensity

Uses metrics such as:

- distance per 90
- sprints per 90
- intensive runs per 90
- top speed
- sprints per kilometre
- intensive runs per kilometre

### Offensive activity

Uses metrics such as:

- goals per 90
- assists per 90
- shots per 90
- shots on target per 90
- crosses per 90
- fouls drawn per 90
- offsides per 90
- penalty attempts per 90

### Defensive activity

Uses metrics such as:

- duels won per 90
- aerial duels won per 90
- tackles won per 90
- interceptions per 90
- fouls committed per 90
- yellow cards per 90

Before PCA, missing values are median-imputed and all features are standardized.
The sign of each PCA axis is oriented so that higher values represent more
activity in that profile dimension.

The preprocessing step generates:

- `player_pca.csv` — data used by the website
- `pca_loadings.csv` — contribution of each feature to its PCA axis
- `pca_summary.csv` — summary of the grouped PCA

## Visualization

The website shows every player as a point in a rotatable 3D Plotly scatter plot.

Position colours:

- **GK** — orange
- **DF** — yellow
- **MF** — green
- **FW** — blue

The visualization supports:

- 3D turntable rotation
- zooming
- player information on hover
- Cartesian grid
- position filtering
- club filtering
- age-range filtering

Filters do not remove unmatched players. Instead, unmatched players remain
visible and become gray.

By default, no filter is active and all players keep their position colour.

## Setup

Run the following commands from the project directory using Python 3.11:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium

## Done by

Developed by **Jossy Grundmann** (jossy.grundmann@tum.de).

This project was created as a personal football data-analysis and visualization project, including:

- data collection and preprocessing
- feature engineering and PCA-based player profiling
- interactive 3D visualization
- filtering and player comparison functionality
- GitHub Pages deployment