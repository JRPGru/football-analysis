#!/usr/bin/env python3

"""
Generic FBref player-statistics downloader.

Downloads player-season statistics from FBref for a user-specified
league and season using soccerdata.

Examples
--------

Bundesliga:

    python data_downloader.py --league "GER-Bundesliga" --season "2025-2026"

Premier League:

    python data_downloader.py --league "ENG-Premier League" --season "2025-2026"

La Liga:

    python data_downloader.py --league "ESP-La Liga" --season "2025-2026"


Output
------

For:

    --league "GER-Bundesliga"
    --season "2025-2026"

the file is saved as:

    data/bundesliga/data_2025_26_all_players.csv


Only FBref data is downloaded.

There is:

    - no Bundesliga.com scraping
    - no Playwright
    - no manually entered URLs
    - no player-name fuzzy matching

Some known empty/unwanted FBref columns are removed before export.
"""


from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import soccerdata as sd
from unidecode import unidecode


# =============================================================================
# Configuration
# =============================================================================


# FBref player-season tables to download.
FBREF_STAT_TYPES = [
    "standard",
    "shooting",
    "playing_time",
    "misc",
    "keeper",
]


# -----------------------------------------------------------------------------
# Columns to exclude
# -----------------------------------------------------------------------------
#
# These fields are currently empty and are not needed by the PCA workflow.
#
# They are removed immediately after the corresponding FBref table has been
# flattened.
#
EXCLUDED_COLUMNS = {
    "fbref_misc_performance_pkwon",
    "fbref_misc_performance_pkcon",
}


# Root directory for downloaded data.
DATA_DIRECTORY = Path("data")


# Delay between FBref requests when pages are not already cached.
REQUEST_DELAY_SECONDS = 6.5


# =============================================================================
# Command-line arguments
# =============================================================================


def parse_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Download FBref player-season statistics "
            "for a specified league and season."
        )
    )

    parser.add_argument(
        "--league",
        required=True,
        help=(
            'soccerdata/FBref league identifier, for example '
            '"GER-Bundesliga" or "ENG-Premier League".'
        ),
    )

    parser.add_argument(
        "--season",
        required=True,
        help=(
            'Season in soccerdata format, for example "2025-2026".'
        ),
    )

    return parser.parse_args()


# =============================================================================
# Output path helpers
# =============================================================================


def league_directory_name(
    league: str,
) -> str:

    """
    Convert a soccerdata league identifier into a clean directory name.

    Examples
    --------

    GER-Bundesliga
        -> bundesliga

    ENG-Premier League
        -> premier_league

    ESP-La Liga
        -> la_liga

    ITA-Serie A
        -> serie_a
    """

    league = str(
        league
    ).strip()

    # Remove country prefix.
    #
    # GER-Bundesliga
    #     -> Bundesliga
    #
    # ENG-Premier League
    #     -> Premier League
    #
    if "-" in league:

        league = league.split(
            "-",
            1,
        )[1]

    league = unidecode(
        league
    ).lower()

    league = re.sub(
        r"[^a-z0-9]+",
        "_",
        league,
    )

    league = re.sub(
        r"_+",
        "_",
        league,
    )

    return league.strip("_")


def season_filename_token(
    season: str,
) -> str:

    """
    Convert season into the project's filename format.

    Examples
    --------

    2025-2026
        -> 2025_26

    2024-2025
        -> 2024_25
    """

    season = str(
        season
    ).strip()

    match = re.fullmatch(
        r"(\d{4})-(\d{4})",
        season,
    )

    if match:

        start_year = match.group(1)
        end_year = match.group(2)

        return (
            f"{start_year}_"
            f"{end_year[-2:]}"
        )

    # Fallback for alternative soccerdata season formats.
    token = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        season,
    )

    return token.strip("_")


def create_output_file(
    league: str,
    season: str,
) -> Path:

    """
    Build output path and create the corresponding league directory.

    Example
    -------

    league = GER-Bundesliga
    season = 2025-2026

    produces:

        data/bundesliga/data_2025_26_all_players.csv
    """

    league_directory = (
        DATA_DIRECTORY
        / league_directory_name(
            league
        )
    )

    league_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    season_token = season_filename_token(
        season
    )

    return (
        league_directory
        / (
            f"data_{season_token}"
            "_all_players.csv"
        )
    )


# =============================================================================
# Column cleaning
# =============================================================================


def clean_token(
    value: object,
) -> str:

    """
    Convert one FBref column-label component into stable snake_case.
    """

    text = str(
        value
    ).strip()

    if (
        not text
        or text.lower() == "nan"
        or text.startswith(
            "Unnamed:"
        )
    ):
        return ""

    text = unidecode(
        text
    )

    text = text.replace(
        "+/-",
        "plus_minus",
    )

    text = text.replace(
        "%",
        "pct",
    )

    text = text.replace(
        "+",
        " plus ",
    )

    text = text.replace(
        "/",
        " per ",
    )

    text = text.replace(
        "-",
        " ",
    )

    text = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        text,
    )

    text = re.sub(
        r"_+",
        "_",
        text,
    )

    return (
        text
        .strip("_")
        .lower()
    )


# =============================================================================
# FBref column flattening
# =============================================================================


def flatten_fbref_columns(
    df: pd.DataFrame,
    stat_type: str,
) -> pd.DataFrame:

    """
    Flatten soccerdata/FBref MultiIndex columns.

    Identifier columns remain:

        league
        season
        team
        player

    Statistics receive explicit source prefixes.

    Examples:

        fbref_standard_playing_time_min
        fbref_shooting_standard_sh
        fbref_playing_time_team_success_plus_minus90
        fbref_misc_performance_int
        fbref_keeper_performance_saves
    """

    df = df.copy()

    flattened: List[str] = []

    for column in df.columns:

        parts = (
            list(column)
            if isinstance(
                column,
                tuple,
            )
            else [column]
        )

        tokens = [
            clean_token(
                part
            )
            for part
            in parts
        ]

        tokens = [
            token
            for token
            in tokens
            if token
        ]

        # ---------------------------------------------------------------------
        # Preserve identifier columns
        # ---------------------------------------------------------------------

        identifier = next(
            (
                token
                for token
                in tokens
                if token in {
                    "league",
                    "season",
                    "team",
                    "player",
                }
            ),
            None,
        )

        if identifier:

            flattened.append(
                identifier
            )

            continue

        # ---------------------------------------------------------------------
        # Statistics
        # ---------------------------------------------------------------------

        suffix = (
            "_".join(
                tokens
            )
            if tokens
            else "value"
        )

        flattened.append(
            f"fbref_"
            f"{clean_token(stat_type)}_"
            f"{suffix}"
        )

    # =========================================================================
    # Guarantee unique column names
    # =========================================================================

    seen: Dict[str, int] = {}

    unique_columns: List[str] = []

    for name in flattened:

        count = seen.get(
            name,
            0,
        )

        seen[name] = count + 1

        if count == 0:

            unique_columns.append(
                name
            )

        else:

            unique_columns.append(
                f"{name}_{count + 1}"
            )

    df.columns = unique_columns

    return df


# =============================================================================
# Exclude unwanted columns
# =============================================================================


def remove_excluded_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:

    """
    Remove explicitly excluded FBref columns.

    Only columns present in the current table are removed.
    """

    excluded_present = [
        column
        for column
        in EXCLUDED_COLUMNS
        if column in df.columns
    ]

    if excluded_present:

        print(
            "  excluding:"
        )

        for column in sorted(
            excluded_present
        ):

            print(
                f"    - {column}"
            )

        df = df.drop(
            columns=excluded_present
        )

    return df


# =============================================================================
# FBref download
# =============================================================================


def get_fbref_data(
    league: str,
    season: str,
) -> pd.DataFrame:

    """
    Download and merge all configured FBref player-season tables.
    """

    print()

    print(
        "Downloading FBref player-season statistics"
    )

    print(
        "==========================================="
    )

    print(
        f"League: {league}"
    )

    print(
        f"Season: {season}"
    )

    print()

    # soccerdata handles FBref URLs automatically.
    fbref = sd.FBref(
        leagues=league,
        seasons=season,
    )

    key_columns = [
        "league",
        "season",
        "team",
        "player",
    ]

    merged: Optional[pd.DataFrame] = None

    # =========================================================================
    # Download each FBref table
    # =========================================================================

    for index, stat_type in enumerate(
        FBREF_STAT_TYPES
    ):

        print(
            f"FBref table: {stat_type}"
        )

        raw = (
            fbref
            .read_player_season_stats(
                stat_type=stat_type
            )
        )

        if raw is None or raw.empty:

            raise RuntimeError(
                f"FBref returned no data "
                f"for stat type '{stat_type}'."
            )

        # ---------------------------------------------------------------------
        # Convert index into ordinary columns and flatten MultiIndex columns.
        # ---------------------------------------------------------------------

        frame = flatten_fbref_columns(
            raw.reset_index(),
            stat_type,
        )

        # ---------------------------------------------------------------------
        # Remove unwanted columns before merge/export.
        # ---------------------------------------------------------------------

        frame = remove_excluded_columns(
            frame
        )

        # ---------------------------------------------------------------------
        # Check expected identifiers
        # ---------------------------------------------------------------------

        missing_keys = [
            key
            for key
            in key_columns
            if key not in frame.columns
        ]

        if missing_keys:

            raise RuntimeError(
                f"FBref '{stat_type}' table "
                f"is missing expected identifier columns: "
                f"{missing_keys}"
            )

        # ---------------------------------------------------------------------
        # Avoid accidental duplicate records
        # ---------------------------------------------------------------------

        frame = frame.drop_duplicates(
            subset=key_columns,
            keep="first",
        )

        print(
            f"  rows:    "
            f"{len(frame):,}"
        )

        print(
            f"  columns: "
            f"{len(frame.columns):,}"
        )

        # ---------------------------------------------------------------------
        # Merge tables
        # ---------------------------------------------------------------------

        if merged is None:

            merged = frame

        else:

            merged = merged.merge(
                frame,
                on=key_columns,
                how="outer",
                validate="one_to_one",
            )

        # ---------------------------------------------------------------------
        # Avoid rapid requests when cache is empty.
        # ---------------------------------------------------------------------

        if (
            index
            < len(FBREF_STAT_TYPES) - 1
        ):

            time.sleep(
                REQUEST_DELAY_SECONDS
            )

    # =========================================================================
    # Validate final dataset
    # =========================================================================

    if (
        merged is None
        or merged.empty
    ):

        raise RuntimeError(
            "FBref returned no player data."
        )

    # -------------------------------------------------------------------------
    # Safety check: make sure excluded columns cannot survive the final merge.
    # -------------------------------------------------------------------------

    merged = remove_excluded_columns(
        merged
    )

    # -------------------------------------------------------------------------
    # Stable ordering
    # -------------------------------------------------------------------------

    merged = (
        merged
        .sort_values(
            [
                "team",
                "player",
            ],
            kind="stable",
        )
        .reset_index(
            drop=True
        )
    )

    # -------------------------------------------------------------------------
    # Put identifiers first
    # -------------------------------------------------------------------------

    identifier_columns = [
        column
        for column
        in [
            "player",
            "team",
            "season",
            "league",
        ]
        if column in merged.columns
    ]

    statistic_columns = [
        column
        for column
        in merged.columns
        if column not in identifier_columns
    ]

    merged = merged[
        identifier_columns
        + statistic_columns
    ]

    return merged


# =============================================================================
# Main
# =============================================================================


def main() -> int:

    args = parse_arguments()

    league = args.league.strip()
    season = args.season.strip()

    output_file = create_output_file(
        league=league,
        season=season,
    )

    try:

        # =====================================================================
        # Download
        # =====================================================================

        final = get_fbref_data(
            league=league,
            season=season,
        )

        # =====================================================================
        # Save
        # =====================================================================
        #
        # Semicolon delimiter and decimal comma remain compatible with the
        # current PCA preprocessing workflow.
        # =====================================================================

        final.to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig",
            sep=";",
            decimal=",",
        )

        # =====================================================================
        # Report
        # =====================================================================

        print()

        print(
            "Download complete"
        )

        print(
            "================="
        )

        print(
            f"League:       "
            f"{league}"
        )

        print(
            f"Season:       "
            f"{season}"
        )

        print(
            f"Players/rows: "
            f"{len(final):,}"
        )

        print(
            f"Columns:      "
            f"{len(final.columns):,}"
        )

        print(
            f"Saved:        "
            f"{output_file.resolve()}"
        )

        return 0

    except Exception as exc:

        print(
            f"\nERROR: {exc}",
            file=sys.stderr,
        )

        print(
            "\nCheck that:\n"
            "  1. the league identifier is valid for soccerdata/FBref\n"
            "  2. the season exists for that league\n"
            "  3. your internet connection is working\n",
            file=sys.stderr,
        )

        return 1


# =============================================================================
# Entry point
# =============================================================================


if __name__ == "__main__":

    raise SystemExit(
        main()
    )