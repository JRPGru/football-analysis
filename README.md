# Football Analysis

A personal project for exploring and visualizing Bundesliga player statistics.

## Current functionality

`data_downloader.py` combines Bundesliga 2025/26 player-season statistics into
`bundesliga_2025_26_all_players.csv`. FBref is the primary source;
Bundesliga.com adds physical and other statistics unavailable from FBref.
Each row represents a player/team/season record. Missing values remain missing,
and ambiguous player-name matches are reported rather than guessed.

## Setup and usage

Run these commands from the project directory using Python 3.11:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
python data_downloader.py
```

Use the same Python interpreter for installation and execution. Downloads require
internet access, and the source websites may change over time.

## Tests

The parser tests run locally and require the installed Chromium browser:

```powershell
python -m unittest test_downloader
```

## Planned visualization

An interactive browser-based 3D scatter plot with selectable metrics, player
information on hover/click, and filters. This visualization is not implemented yet.

See [agent.md](agent.md) for source priorities, matching rules, and project scope.

See [CSV glossary (German)](CSV_GLOSSAR_DE.md) for explanations of all 110 CSV
columns, abbreviations, units, examples, and interpretation notes.
