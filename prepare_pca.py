#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from unidecode import unidecode


# =============================================================================
# USER CONFIGURATION
# =============================================================================
#
# This is the main section you should edit.
#
# Use EXACT column names from data_YYYY_YY_all_players.csv / the FBref glossary.
#
# The ORDER of the groups determines the plot axes:
#
#     first group  -> PC1 -> X
#     second group -> PC2 -> Y
#     third group  -> PC3 -> Z
#
# "name" is the human-readable name that will later be shown on the plot axis.
#
# Example:
#
#     {
#         "name": "Shooting",
#         "metrics": [
#             "fbref_shooting_standard_sh_per_90",
#             ...
#         ],
#     }
#
# IMPORTANT:
#
# The values themselves keep their native meaning.
#
# - totals/counts remain totals
# - per-90 values remain per-90 values
# - percentages remain percentages
# - ratios remain ratios
#
# The script does NOT automatically turn totals into per-90 values.
#
# =============================================================================


PCA_GROUPS = [

    # =========================================================================
    # PC1 / X axis
    # =========================================================================

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


    # =========================================================================
    # PC2 / Y axis
    # =========================================================================

    {
        "name": "Team Success",

        "metrics": [

            "fbref_playing_time_team_success_ppm",

            "fbref_playing_time_team_success_plus_minus90",

            "fbref_playing_time_team_success_on_off",

        ],
    },


    # =========================================================================
    # PC3 / Z axis
    # =========================================================================

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


# Players must have STRICTLY more than this number of minutes.
MIN_MINUTES = 400


# =============================================================================
# Advanced configuration
# =============================================================================

MINUTES_COLUMN = "fbref_standard_playing_time_min"

POSITION_COLUMN = "fbref_standard_pos"

AGE_COLUMN = "fbref_standard_age"


# =============================================================================
# Project paths
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIRECTORY = PROJECT_ROOT / "data"

VIZ_DIRECTORY = PROJECT_ROOT / "Viz"

MANIFEST_FILE = VIZ_DIRECTORY / "data_sources.json"


# =============================================================================
# Command line
# =============================================================================


def parse_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser(

        description=(
            "Prepare configurable grouped PCA data "
            "from downloaded FBref statistics."
        )

    )


    parser.add_argument(

        "--league",

        required=True,

        help=(
            'League identifier, for example '
            '"GER-Bundesliga".'
        ),

    )


    parser.add_argument(

        "--season",

        required=True,

        help=(
            'Season, for example '
            '"2025-2026".'
        ),

    )


    return parser.parse_args()


# =============================================================================
# Path helpers
# =============================================================================


def league_directory_name(
    league: str
) -> str:

    league = str(
        league
    ).strip()


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


def league_display_name(
    league: str
) -> str:

    league = str(
        league
    ).strip()


    if re.match(

        r"^[A-Z]{3}-",

        league,

    ):

        return league.split(
            "-",
            1,
        )[1]


    return league


def season_filename_token(
    season: str
) -> str:

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


    return re.sub(

        r"[^A-Za-z0-9]+",

        "_",

        season,

    ).strip("_")


def season_display_name(
    season: str
) -> str:

    season = str(
        season
    ).strip()


    match = re.fullmatch(

        r"(\d{4})-(\d{4})",

        season,

    )


    if match:

        return (
            f"{match.group(1)}/"
            f"{match.group(2)[-2:]}"
        )


    return season


# =============================================================================
# Configuration validation
# =============================================================================


def validate_pca_configuration():

    if len(PCA_GROUPS) != 3:

        raise ValueError(

            "Exactly 3 PCA groups are required for the 3D visualization.\n\n"

            f"Currently configured: {len(PCA_GROUPS)}"

        )


    names = []


    for index, group in enumerate(
        PCA_GROUPS,
        start=1,
    ):

        if "name" not in group:

            raise ValueError(

                f"PCA group {index} has no 'name'."

            )


        if "metrics" not in group:

            raise ValueError(

                f"PCA group {index} has no 'metrics' list."

            )


        name = str(
            group["name"]
        ).strip()


        if not name:

            raise ValueError(

                f"PCA group {index} has an empty name."

            )


        metrics = group[
            "metrics"
        ]


        if not isinstance(
            metrics,
            list,
        ):

            raise ValueError(

                f"PCA group '{name}' metrics must be a list."

            )


        if len(metrics) < 2:

            raise ValueError(

                f"PCA group '{name}' needs at least 2 metrics."

            )


        if len(metrics) != len(set(metrics)):

            raise ValueError(

                f"PCA group '{name}' contains duplicate metrics."

            )


        names.append(
            name
        )


    if len(names) != len(set(names)):

        raise ValueError(

            "Every PCA group must have a unique name."

        )


    all_metrics = get_all_selected_metrics()


    duplicates = {

        metric

        for metric
        in all_metrics

        if all_metrics.count(metric) > 1

    }


    if duplicates:

        raise ValueError(

            "The same metric is currently used in multiple PCA groups:\n"

            +

            "\n".join(

                f"  - {metric}"

                for metric
                in sorted(duplicates)

            )

        )


def get_all_selected_metrics() -> list[str]:

    return [

        metric

        for group
        in PCA_GROUPS

        for metric
        in group["metrics"]

    ]


# =============================================================================
# Numeric helpers
# =============================================================================


def numeric(
    series: pd.Series
) -> pd.Series:

    return pd.to_numeric(

        series,

        errors="coerce",

    )


def weighted_average(
    values: pd.Series,
    weights: pd.Series,
):

    values = numeric(
        values
    )


    weights = numeric(
        weights
    )


    valid = (

        values.notna()

        & weights.notna()

        & (weights > 0)

    )


    if not valid.any():

        return np.nan


    return float(

        np.average(

            values[valid],

            weights=weights[valid],

        )

    )


# =============================================================================
# Metric type detection
# =============================================================================
#
# We need this only when a player has records for multiple clubs.
#
# FBref metrics fall broadly into:
#
#   COUNT
#       Goals, shots, fouls, tackles, etc.
#
#       -> sum the club rows
#
#
#   RATE / RATIO / PERCENTAGE
#       per-90 values, percentages, averages, ratios, PPM, On-Off
#
#       -> combine club rows with a minutes-weighted average
#
#
# This does NOT change a metric from total to per-90 or vice versa.
# It only determines how multiple club rows are combined.
#
# =============================================================================


def is_non_additive_metric(
    column: str
) -> bool:

    column = column.lower()


    # -------------------------------------------------------------------------
    # Percentage fields
    # -------------------------------------------------------------------------

    if (

        column.endswith("pct")

        or "_pct_" in column

    ):

        return True


    # -------------------------------------------------------------------------
    # Explicit per-90 fields
    # -------------------------------------------------------------------------

    if (

        "_per_90" in column

        or "_per_90_minutes_" in column

        or column.endswith("90")

    ):

        return True


    # -------------------------------------------------------------------------
    # Ratios / averages
    # -------------------------------------------------------------------------

    ratio_patterns = [

        "_g_per_sh",

        "_g_per_sot",

        "_mn_per_mp",

        "_mn_per_start",

        "_mn_per_sub",

        "_ppm",

        "_on_off",

    ]


    if any(

        pattern in column

        for pattern
        in ratio_patterns

    ):

        return True


    return False


def combine_metric(
    group: pd.DataFrame,
    column: str,
):

    values = numeric(
        group[column]
    )


    if is_non_additive_metric(
        column
    ):

        return weighted_average(

            values,

            group["_minutes"],

        )


    # Counts/totals are additive across clubs.

    return values.sum(
        min_count=1
    )


# =============================================================================
# Position classification
# =============================================================================


def classify_position(
    position
):

    if pd.isna(position):

        return None


    primary = re.split(

        r"[,\s/;-]+",

        str(position)
        .upper()
        .strip(),

    )[0]


    if primary in {

        "GK",
        "G",

    }:

        return "GK"


    if primary in {

        "DF",
        "DEF",
        "D",

        "FB",
        "CB",
        "LB",
        "RB",

    }:

        return "DF"


    if primary in {

        "MF",
        "MID",
        "M",

        "DM",
        "CM",
        "AM",

        "LM",
        "RM",
        "WM",

    }:

        return "MF"


    if primary in {

        "FW",
        "FWD",
        "F",

        "ST",

        "LW",
        "RW",

    }:

        return "FW"


    return None


# =============================================================================
# Input validation
# =============================================================================


def require_columns(
    df: pd.DataFrame
):

    required = {

        "player",

        "team",

        MINUTES_COLUMN,

        POSITION_COLUMN,

        AGE_COLUMN,

        *get_all_selected_metrics(),

    }


    missing = sorted(

        required
        - set(df.columns)

    )


    if missing:

        raise ValueError(

            "The selected PCA configuration contains columns "
            "that do not exist in the input CSV:\n\n"

            +

            "\n".join(

                f"  - {column}"

                for column
                in missing

            )

            +

            "\n\nUse the exact column names from the CSV / FBref glossary."

        )


# =============================================================================
# Combine player rows
# =============================================================================


def combine_player_rows(
    df: pd.DataFrame
) -> pd.DataFrame:

    selected_metrics = (
        get_all_selected_metrics()
    )


    players = []


    for (
        player_name,
        group
    ) in df.groupby(

        "player",

        sort=False,

    ):


        group = group.copy()


        group[
            "_minutes"
        ] = (

            numeric(
                group[
                    MINUTES_COLUMN
                ]
            )

            .fillna(0)

        )


        total_minutes = float(

            group[
                "_minutes"
            ].sum()

        )


        # ---------------------------------------------------------------------
        # Minimum playing time
        # ---------------------------------------------------------------------

        if total_minutes <= MIN_MINUTES:

            continue


        # ---------------------------------------------------------------------
        # Metadata comes from the club row with the most minutes.
        # ---------------------------------------------------------------------

        primary_row = group.loc[

            group[
                "_minutes"
            ].idxmax()

        ]


        raw_position = primary_row.get(
            POSITION_COLUMN
        )


        teams = " / ".join(

            dict.fromkeys(

                group[
                    "team"
                ]

                .dropna()

                .astype(str)

                .str.strip()

                .loc[
                    lambda values:
                        values.ne("")
                ]

            )

        )


        row = {

            "player":
                str(
                    player_name
                ).strip(),

            "team":
                teams,

            "position":
                (
                    ""
                    if pd.isna(raw_position)
                    else str(
                        raw_position
                    ).strip()
                ),

            "position_group":
                classify_position(
                    raw_position
                ),

            "age":
                pd.to_numeric(

                    primary_row.get(
                        AGE_COLUMN
                    ),

                    errors="coerce",

                ),

            "minutes":
                total_minutes,

        }


        # ---------------------------------------------------------------------
        # Selected PCA metrics
        # ---------------------------------------------------------------------

        for metric in selected_metrics:

            row[
                metric
            ] = combine_metric(

                group,

                metric,

            )


        players.append(
            row
        )


    return pd.DataFrame(
        players
    )


# =============================================================================
# PCA
# =============================================================================


def fit_pca_group(

    players: pd.DataFrame,

    group_index: int,

    group_config: dict,

):

    group_name = str(
        group_config["name"]
    ).strip()


    metrics = list(
        group_config["metrics"]
    )


    axis = (
        f"PC{group_index}"
    )


    X_original = players[
        metrics
    ].copy()


    # =========================================================================
    # Missing-data counts
    # =========================================================================

    observed_count = (

        X_original
        .notna()
        .sum(
            axis=1
        )

    )


    imputed_count = (

        len(metrics)
        - observed_count

    )


    # =========================================================================
    # Completely empty metrics
    # =========================================================================

    empty_metrics = [

        metric

        for metric
        in metrics

        if (
            X_original[
                metric
            ]

            .notna()

            .sum()

            == 0
        )

    ]


    usable_metrics = [

        metric

        for metric
        in metrics

        if metric
        not in empty_metrics

    ]


    if empty_metrics:

        print()

        print(

            f"{axis} ({group_name}): "
            "dropping completely empty metrics:"

        )


        for metric in empty_metrics:

            print(
                f"  - {metric}"
            )


    if not usable_metrics:

        raise ValueError(

            f"{axis} ({group_name}) has no usable metrics."

        )


    # =========================================================================
    # Median imputation
    # =========================================================================

    X_usable = X_original[
        usable_metrics
    ]


    imputer = SimpleImputer(

        strategy="median",

    )


    X_imputed = imputer.fit_transform(

        X_usable

    )


    imputation_medians = dict(

        zip(

            usable_metrics,

            imputer.statistics_,

        )

    )


    # =========================================================================
    # Remove zero-variance metrics
    # =========================================================================

    variances = np.var(

        X_imputed,

        axis=0,

    )


    keep_mask = (
        variances > 0
    )


    used_metrics = [

        metric

        for metric, keep
        in zip(
            usable_metrics,
            keep_mask,
        )

        if keep

    ]


    zero_variance_metrics = [

        metric

        for metric, keep
        in zip(
            usable_metrics,
            keep_mask,
        )

        if not keep

    ]


    if zero_variance_metrics:

        print()

        print(

            f"{axis} ({group_name}): "
            "dropping zero-variance metrics:"

        )


        for metric in zero_variance_metrics:

            print(
                f"  - {metric}"
            )


    if not used_metrics:

        raise ValueError(

            f"{axis} ({group_name}) has no varying metrics."

        )


    X_used = X_imputed[
        :,
        keep_mask
    ]


    # =========================================================================
    # Standardize metrics
    # =========================================================================

    scaler = StandardScaler()


    X_scaled = scaler.fit_transform(

        X_used

    )


    # =========================================================================
    # PCA
    # =========================================================================

    pca = PCA(

        n_components=1

    )


    raw_scores = (

        pca.fit_transform(
            X_scaled
        )[:, 0]

    )


    loadings = (

        pca.components_[0]
        .copy()

    )


    # =========================================================================
    # Orient sign
    # =========================================================================
    #
    # PCA sign is mathematically arbitrary.
    #
    # To make the direction stable and intuitive, positive PC values are
    # oriented toward the average standardized value of the selected metrics.
    #
    # =============================================================================

    average_metric_activity = (

        X_scaled.mean(
            axis=1
        )

    )


    correlation = np.corrcoef(

        raw_scores,

        average_metric_activity,

    )[0, 1]


    if (

        np.isfinite(
            correlation
        )

        and correlation < 0

    ):

        raw_scores *= -1

        loadings *= -1


    # =========================================================================
    # Standardize PCA score itself
    # =========================================================================

    score_std = raw_scores.std(
        ddof=0
    )


    if score_std == 0:

        scores = np.zeros_like(
            raw_scores
        )


    else:

        scores = (

            raw_scores
            - raw_scores.mean()

        ) / score_std


    # =========================================================================
    # Loadings output
    # =========================================================================

    loading_map = dict(

        zip(

            used_metrics,

            loadings,

        )

    )


    loading_rows = []


    for metric in metrics:


        if metric in used_metrics:

            used = True

            drop_reason = ""

            loading = float(

                loading_map[
                    metric
                ]

            )

            imputation_median = float(

                imputation_medians[
                    metric
                ]

            )


        elif metric in empty_metrics:

            used = False

            drop_reason = (
                "all_missing"
            )

            loading = 0.0

            imputation_median = np.nan


        else:

            used = False

            drop_reason = (
                "zero_variance"
            )

            loading = 0.0

            imputation_median = float(

                imputation_medians[
                    metric
                ]

            )


        loading_rows.append({

            "axis":
                axis,

            "group_name":
                group_name,

            "metric":
                metric,

            "loading":
                loading,

            "used_in_pca":
                used,

            "drop_reason":
                drop_reason,

            "observed_pct":
                float(

                    players[
                        metric
                    ]

                    .notna()

                    .mean()

                    * 100

                ),

            "imputation_median":
                imputation_median,

        })


    explained_variance_pct = float(

        pca.explained_variance_ratio_[0]

        * 100

    )


    loading_table = pd.DataFrame(

        loading_rows

    )


    loading_table[
        "explained_variance_pct"
    ] = explained_variance_pct


    return {

        "axis":
            axis,

        "name":
            group_name,

        "scores":
            scores,

        "metrics":
            metrics,

        "used_metrics":
            used_metrics,

        "observed_count":
            observed_count,

        "imputed_count":
            imputed_count,

        "loadings":
            loading_table,

        "explained_variance_pct":
            explained_variance_pct,

    }


# =============================================================================
# Visualization manifest
# =============================================================================


def read_prepared_metadata(
    file: Path
):

    try:

        frame = pd.read_csv(

            file,

            nrows=1,

        )

    except Exception as exc:

        print(

            f"Manifest warning: "
            f"could not read {file}: {exc}"

        )

        return None


    if frame.empty:

        return None


    required = [

        "league",

        "season",

    ]


    if any(

        column not in frame.columns

        for column
        in required

    ):

        return None


    league = str(

        frame.iloc[0][
            "league"
        ]

    ).strip()


    season = str(

        frame.iloc[0][
            "season"
        ]

    ).strip()


    axis_labels = {}


    for index in range(
        1,
        4,
    ):

        column = (
            f"PC{index}_label"
        )


        if column in frame.columns:

            value = str(

                frame.iloc[0][
                    column
                ]

            ).strip()


            if (
                value
                and value.lower()
                != "nan"
            ):

                axis_labels[
                    f"PC{index}"
                ] = value


    return {

        "league":
            league,

        "season":
            season,

        "axis_labels":
            axis_labels,

    }


def build_visualization_manifest():

    VIZ_DIRECTORY.mkdir(

        parents=True,

        exist_ok=True,

    )


    files = sorted(

        DATA_DIRECTORY.rglob(

            "player_pca_fbref_*.csv"

        )

    )


    sources = []


    for file in files:


        metadata = (
            read_prepared_metadata(
                file
            )
        )


        if metadata is None:

            print(

                f"Manifest warning: "
                f"skipping {file}"

            )

            continue


        league = metadata[
            "league"
        ]


        season = metadata[
            "season"
        ]


        relative_path = os.path.relpath(

            file,

            VIZ_DIRECTORY,

        ).replace(

            os.sep,

            "/",

        )


        sources.append({

            "id":
                (
                    f"{league_directory_name(league)}-"
                    f"{season_filename_token(season)}"
                ),

            "league":
                league,

            "league_name":
                league_display_name(
                    league
                ),

            "season":
                season,

            "season_label":
                season_display_name(
                    season
                ),

            "axis_labels":
                metadata[
                    "axis_labels"
                ],

            "path":
                relative_path,

            "modified":
                datetime.fromtimestamp(

                    file.stat().st_mtime,

                    tz=timezone.utc,

                ).isoformat(),

        })


    # -------------------------------------------------------------------------
    # Remove duplicate league/season entries
    # -------------------------------------------------------------------------

    unique = {}


    for source in sources:

        key = (

            source[
                "league"
            ],

            source[
                "season"
            ],

        )


        unique[
            key
        ] = source


    sources = list(
        unique.values()
    )


    sources.sort(

        key=lambda source: (

            source[
                "league_name"
            ].lower(),

            source[
                "season"
            ],

        )

    )


    manifest = {

        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "sources":
            sources,

    }


    MANIFEST_FILE.write_text(

        json.dumps(

            manifest,

            indent=2,

            ensure_ascii=False,

        ),

        encoding="utf-8",

    )


    print()

    print(
        f"Visualization manifest: "
        f"{MANIFEST_FILE}"
    )


    print(
        f"Available datasets: "
        f"{len(sources)}"
    )


    for source in sources:

        labels = source[
            "axis_labels"
        ]


        print(

            f"  - "
            f"{source['league_name']} "
            f"{source['season_label']}"

        )


        print(

            f"      PC1: "
            f"{labels.get('PC1', 'PC1')}"

        )


        print(

            f"      PC2: "
            f"{labels.get('PC2', 'PC2')}"

        )


        print(

            f"      PC3: "
            f"{labels.get('PC3', 'PC3')}"

        )


# =============================================================================
# Main
# =============================================================================


def main():

    validate_pca_configuration()


    args = parse_arguments()


    league = args.league.strip()

    season = args.season.strip()


    league_directory = (

        DATA_DIRECTORY

        / league_directory_name(
            league
        )

    )


    season_token = season_filename_token(
        season
    )


    input_file = (

        league_directory

        / (
            f"data_{season_token}"
            "_all_players.csv"
        )

    )


    output_file = (

        league_directory

        / (
            f"player_pca_fbref_"
            f"{season_token}.csv"
        )

    )


    loadings_file = (

        league_directory

        / (
            f"pca_loadings_fbref_"
            f"{season_token}.csv"
        )

    )


    summary_file = (

        league_directory

        / (
            f"pca_summary_fbref_"
            f"{season_token}.csv"
        )

    )


    # =========================================================================
    # Input
    # =========================================================================

    if not input_file.exists():

        raise FileNotFoundError(

            f"Could not find:\n"
            f"  {input_file}\n\n"

            f"Download it first with:\n"

            f'  python data_downloader.py '
            f'--league "{league}" '
            f'--season "{season}"'

        )


    print()

    print(
        "Preparing configurable FBref PCA"
    )


    print(
        "================================"
    )


    print(
        f"League: {league}"
    )


    print(
        f"Season: {season}"
    )


    print(
        f"Input:  {input_file}"
    )


    print()

    print(
        "Configured axes:"
    )


    for index, group in enumerate(

        PCA_GROUPS,

        start=1,

    ):

        print()

        print(

            f"PC{index}: "
            f"{group['name']}"

        )


        for metric in group[
            "metrics"
        ]:

            print(
                f"  - {metric}"
            )


    # =========================================================================
    # Read raw CSV
    # =========================================================================

    df = pd.read_csv(

        input_file,

        sep=";",

        decimal=",",

    )


    require_columns(
        df
    )


    # =========================================================================
    # Build player table
    # =========================================================================

    players = combine_player_rows(
        df
    )


    if players.empty:

        raise ValueError(

            f"No players have more than "
            f"{MIN_MINUTES} minutes."

        )


    # =========================================================================
    # Add source metadata
    # =========================================================================

    players.insert(

        0,

        "season",

        season,

    )


    players.insert(

        0,

        "league",

        league,

    )


    # =========================================================================
    # Fit all PCA groups
    # =========================================================================

    pca_results = []


    for index, group in enumerate(

        PCA_GROUPS,

        start=1,

    ):

        result = fit_pca_group(

            players,

            index,

            group,

        )


        pca_results.append(
            result
        )


        axis = result[
            "axis"
        ]


        # ---------------------------------------------------------------------
        # Coordinate
        # ---------------------------------------------------------------------

        players[
            axis
        ] = result[
            "scores"
        ]


        # ---------------------------------------------------------------------
        # Axis display name
        # ---------------------------------------------------------------------

        players[
            f"{axis}_label"
        ] = result[
            "name"
        ]


        # ---------------------------------------------------------------------
        # Missing-data information
        # ---------------------------------------------------------------------

        players[
            f"{axis}_observed_features"
        ] = result[
            "observed_count"
        ]


        players[
            f"{axis}_imputed_features"
        ] = result[
            "imputed_count"
        ]


    # =========================================================================
    # Overall missing-data count
    # =========================================================================

    selected_metrics = (
        get_all_selected_metrics()
    )


    players[
        "observed_features"
    ] = (

        players[
            selected_metrics
        ]

        .notna()

        .sum(
            axis=1
        )

    )


    players[
        "imputed_features"
    ] = (

        len(
            selected_metrics
        )

        - players[
            "observed_features"
        ]

    )


    # =========================================================================
    # Export player PCA
    # =========================================================================

    output_columns = [

        "league",

        "season",

        "player",

        "team",

        "position",

        "position_group",

        "age",

        "minutes",


        # -------------------------------------------------------------
        # PCA coordinates
        # -------------------------------------------------------------

        "PC1",

        "PC2",

        "PC3",


        # -------------------------------------------------------------
        # Human-readable axis names
        # -------------------------------------------------------------

        "PC1_label",

        "PC2_label",

        "PC3_label",


        # -------------------------------------------------------------
        # Overall missing-data info
        # -------------------------------------------------------------

        "observed_features",

        "imputed_features",


        # -------------------------------------------------------------
        # Per-axis missing-data info
        # -------------------------------------------------------------

        "PC1_observed_features",

        "PC1_imputed_features",

        "PC2_observed_features",

        "PC2_imputed_features",

        "PC3_observed_features",

        "PC3_imputed_features",


        # -------------------------------------------------------------
        # Exact selected FBref columns
        # -------------------------------------------------------------

        *selected_metrics,

    ]


    players[
        output_columns
    ].to_csv(

        output_file,

        index=False,

    )


    # =========================================================================
    # Export loadings
    # =========================================================================

    loadings = pd.concat(

        [

            result[
                "loadings"
            ]

            for result
            in pca_results

        ],

        ignore_index=True,

    )


    loadings.to_csv(

        loadings_file,

        index=False,

    )


    # =========================================================================
    # Export PCA summary
    # =========================================================================

    summary_rows = []


    for result in pca_results:

        summary_rows.append({

            "axis":
                result[
                    "axis"
                ],

            "name":
                result[
                    "name"
                ],

            "feature_count_requested":
                len(
                    result[
                        "metrics"
                    ]
                ),

            "feature_count_used":
                len(
                    result[
                        "used_metrics"
                    ]
                ),

            "explained_variance_pct":
                result[
                    "explained_variance_pct"
                ],

            "metrics":
                " | ".join(
                    result[
                        "metrics"
                    ]
                ),

        })


    summary = pd.DataFrame(

        summary_rows

    )


    summary.to_csv(

        summary_file,

        index=False,

    )


    # =========================================================================
    # Rebuild visualization manifest
    # =========================================================================

    build_visualization_manifest()


    # =========================================================================
    # Console report
    # =========================================================================

    print()

    print(
        "PCA complete"
    )


    print(
        "============"
    )


    print()

    print(

        f"Input rows: "
        f"{len(df)}"

    )


    print(

        f"Players > {MIN_MINUTES} min: "
        f"{len(players)}"

    )


    print()

    print(
        "PCA axes:"
    )


    for result in pca_results:

        print()

        print(

            f"  {result['axis']}: "
            f"{result['name']}"

        )


        print(

            f"    Explained variance: "
            f"{result['explained_variance_pct']:.1f}%"

        )


        print(

            f"    Metrics used: "
            f"{len(result['used_metrics'])}"

        )


    print()

    print(
        "Loadings:"
    )


    for result in pca_results:

        print()

        print(

            f"{result['axis']} — "
            f"{result['name']}"

        )


        print(

            result[
                "loadings"
            ][

                [
                    "metric",
                    "loading",
                    "used_in_pca",
                ]

            ]

            .sort_values(

                "loading",

                ascending=False,

            )

            .to_string(
                index=False
            )

        )


    print()

    print(
        f"Saved: {output_file}"
    )


    print(
        f"Saved: {loadings_file}"
    )


    print(
        f"Saved: {summary_file}"
    )


# =============================================================================
# Entry point
# =============================================================================


if __name__ == "__main__":

    main()