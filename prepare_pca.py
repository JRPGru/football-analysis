#!/usr/bin/env python3

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
# Project paths
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIRECTORY = PROJECT_ROOT / "data"
VIZ_DIRECTORY = PROJECT_ROOT / "Viz"
MANIFEST_FILE = VIZ_DIRECTORY / "data_sources.json"


# =============================================================================
# Configuration
# =============================================================================

MIN_MINUTES = 400

MINUTES_COLUMN = "fbref_standard_playing_time_min"
POSITION_COLUMN = "fbref_standard_pos"
AGE_COLUMN = "fbref_standard_age"


# =============================================================================
# PCA features
# =============================================================================

PCA1_FEATURES = [
    "shooting_goals_per90",
    "shots_per90",
    "shots_on_target_per90",
    "shots_on_target_pct",
    "goals_per_shot",
    "goals_per_shot_on_target",
    "penalties_scored_per90",
    "penalty_attempts_per90",
]


PCA2_FEATURES = [
    "points_per_match",
    "team_goals_for_per90",
    "team_goals_against_per90",
    "plus_minus_per90",
    "on_off_per90",
]


PCA3_FEATURES = [
    "yellow_cards_per90",
    "red_cards_per90",
    "second_yellow_cards_per90",
    "fouls_committed_per90",
    "fouls_drawn_per90",
    "offsides_per90",
    "crosses_per90",
    "interceptions_per90",
    "tackles_won_per90",
    "own_goals_per90",
]


# =============================================================================
# Source columns
# =============================================================================

SHOOTING_COLUMNS = {
    "goals":
        "fbref_shooting_standard_gls",

    "shots":
        "fbref_shooting_standard_sh",

    "shots_on_target":
        "fbref_shooting_standard_sot",

    "penalties_scored":
        "fbref_shooting_standard_pk",

    "penalty_attempts":
        "fbref_shooting_standard_pkatt",
}


TEAM_SUCCESS_COLUMNS = {
    "points_per_match":
        "fbref_playing_time_team_success_ppm",

    "goals_for":
        "fbref_playing_time_team_success_ong",

    "goals_against":
        "fbref_playing_time_team_success_onga",

    "plus_minus":
        "fbref_playing_time_team_success_plus_minus",

    "on_off":
        "fbref_playing_time_team_success_on_off",
}


MISC_COLUMNS = {
    "yellow_cards":
        "fbref_misc_performance_crdy",

    "red_cards":
        "fbref_misc_performance_crdr",

    "second_yellow_cards":
        "fbref_misc_performance_2crdy",

    "fouls_committed":
        "fbref_misc_performance_fls",

    "fouls_drawn":
        "fbref_misc_performance_fld",

    "offsides":
        "fbref_misc_performance_off",

    "crosses":
        "fbref_misc_performance_crs",

    "interceptions":
        "fbref_misc_performance_int",

    "tackles_won":
        "fbref_misc_performance_tklw",

    "own_goals":
        "fbref_misc_performance_og",
}


# =============================================================================
# CLI
# =============================================================================


def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Prepare grouped PCA data from FBref statistics."
    )

    parser.add_argument(
        "--league",
        required=True,
        help='Example: "GER-Bundesliga"',
    )

    parser.add_argument(
        "--season",
        required=True,
        help='Example: "2025-2026"',
    )

    return parser.parse_args()


# =============================================================================
# Naming helpers
# =============================================================================


def league_directory_name(league: str) -> str:

    league = league.strip()

    if "-" in league:
        league = league.split("-", 1)[1]

    league = unidecode(league).lower()

    league = re.sub(
        r"[^a-z0-9]+",
        "_",
        league,
    )

    return league.strip("_")


def league_display_name(league: str) -> str:

    league = league.strip()

    if re.match(
        r"^[A-Z]{3}-",
        league,
    ):
        return league.split("-", 1)[1]

    return league


def season_filename_token(season: str) -> str:

    season = season.strip()

    match = re.fullmatch(
        r"(\d{4})-(\d{4})",
        season,
    )

    if match:
        return (
            f"{match.group(1)}_"
            f"{match.group(2)[-2:]}"
        )

    return re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        season,
    ).strip("_")


def season_display_name(season: str) -> str:

    match = re.fullmatch(
        r"(\d{4})-(\d{4})",
        season.strip(),
    )

    if match:
        return (
            f"{match.group(1)}/"
            f"{match.group(2)[-2:]}"
        )

    return season


# =============================================================================
# Numeric helpers
# =============================================================================


def numeric(series: pd.Series) -> pd.Series:

    return pd.to_numeric(
        series,
        errors="coerce",
    )


def safe_per90(
    value,
    minutes,
):

    if (
        pd.isna(value)
        or minutes <= 0
    ):
        return np.nan

    return (
        float(value)
        * 90
        / float(minutes)
    )


def safe_ratio(
    numerator,
    denominator,
):

    if (
        pd.isna(numerator)
        or pd.isna(denominator)
        or float(denominator) <= 0
    ):
        return np.nan

    return (
        float(numerator)
        / float(denominator)
    )


def safe_percentage(
    numerator,
    denominator,
):

    value = safe_ratio(
        numerator,
        denominator,
    )

    return (
        value * 100
        if pd.notna(value)
        else np.nan
    )


def weighted_average(
    values,
    weights,
):

    values = numeric(values)
    weights = numeric(weights)

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
# Position
# =============================================================================


def classify_position(position):

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


def require_columns(df):

    required = {
        "player",
        "team",
        MINUTES_COLUMN,
        POSITION_COLUMN,
        AGE_COLUMN,
        *SHOOTING_COLUMNS.values(),
        *TEAM_SUCCESS_COLUMNS.values(),
        *MISC_COLUMNS.values(),
    }

    missing = sorted(
        required
        - set(df.columns)
    )

    if missing:

        raise ValueError(
            "Input CSV is missing required columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
        )


# =============================================================================
# Player aggregation
# =============================================================================


def combine_player_rows(df):

    players = []

    for player_name, group in df.groupby(
        "player",
        sort=False,
    ):

        group = group.copy()

        group["_minutes"] = (
            numeric(
                group[MINUTES_COLUMN]
            )
            .fillna(0)
        )

        total_minutes = float(
            group["_minutes"].sum()
        )

        if total_minutes <= MIN_MINUTES:
            continue

        primary = group.loc[
            group["_minutes"].idxmax()
        ]

        raw_position = primary.get(
            POSITION_COLUMN
        )

        teams = " / ".join(
            dict.fromkeys(
                group["team"]
                .dropna()
                .astype(str)
                .str.strip()
                .loc[
                    lambda x:
                        x.ne("")
                ]
            )
        )

        row = {
            "player":
                str(player_name).strip(),

            "team":
                teams,

            "position":
                ""
                if pd.isna(raw_position)
                else str(raw_position).strip(),

            "position_group":
                classify_position(
                    raw_position
                ),

            "age":
                pd.to_numeric(
                    primary.get(
                        AGE_COLUMN
                    ),
                    errors="coerce",
                ),

            "minutes":
                total_minutes,
        }

        # ---------------------------------------------------------------------
        # PCA1 — Shooting
        # ---------------------------------------------------------------------

        goals = numeric(
            group[
                SHOOTING_COLUMNS["goals"]
            ]
        ).sum(
            min_count=1
        )

        shots = numeric(
            group[
                SHOOTING_COLUMNS["shots"]
            ]
        ).sum(
            min_count=1
        )

        sot = numeric(
            group[
                SHOOTING_COLUMNS["shots_on_target"]
            ]
        ).sum(
            min_count=1
        )

        penalties = numeric(
            group[
                SHOOTING_COLUMNS["penalties_scored"]
            ]
        ).sum(
            min_count=1
        )

        penalty_attempts = numeric(
            group[
                SHOOTING_COLUMNS["penalty_attempts"]
            ]
        ).sum(
            min_count=1
        )

        row["shooting_goals_per90"] = safe_per90(
            goals,
            total_minutes,
        )

        row["shots_per90"] = safe_per90(
            shots,
            total_minutes,
        )

        row["shots_on_target_per90"] = safe_per90(
            sot,
            total_minutes,
        )

        row["shots_on_target_pct"] = safe_percentage(
            sot,
            shots,
        )

        row["goals_per_shot"] = safe_ratio(
            goals,
            shots,
        )

        row["goals_per_shot_on_target"] = safe_ratio(
            goals,
            sot,
        )

        row["penalties_scored_per90"] = safe_per90(
            penalties,
            total_minutes,
        )

        row["penalty_attempts_per90"] = safe_per90(
            penalty_attempts,
            total_minutes,
        )

        # ---------------------------------------------------------------------
        # PCA2 — Team Success
        # ---------------------------------------------------------------------

        goals_for = numeric(
            group[
                TEAM_SUCCESS_COLUMNS["goals_for"]
            ]
        ).sum(
            min_count=1
        )

        goals_against = numeric(
            group[
                TEAM_SUCCESS_COLUMNS["goals_against"]
            ]
        ).sum(
            min_count=1
        )

        plus_minus = numeric(
            group[
                TEAM_SUCCESS_COLUMNS["plus_minus"]
            ]
        ).sum(
            min_count=1
        )

        row["points_per_match"] = weighted_average(
            group[
                TEAM_SUCCESS_COLUMNS["points_per_match"]
            ],
            group["_minutes"],
        )

        row["team_goals_for_per90"] = safe_per90(
            goals_for,
            total_minutes,
        )

        row["team_goals_against_per90"] = safe_per90(
            goals_against,
            total_minutes,
        )

        row["plus_minus_per90"] = safe_per90(
            plus_minus,
            total_minutes,
        )

        row["on_off_per90"] = weighted_average(
            group[
                TEAM_SUCCESS_COLUMNS["on_off"]
            ],
            group["_minutes"],
        )

        # ---------------------------------------------------------------------
        # PCA3 — Misc
        # ---------------------------------------------------------------------

        misc_map = {
            "yellow_cards_per90":
                "yellow_cards",

            "red_cards_per90":
                "red_cards",

            "second_yellow_cards_per90":
                "second_yellow_cards",

            "fouls_committed_per90":
                "fouls_committed",

            "fouls_drawn_per90":
                "fouls_drawn",

            "offsides_per90":
                "offsides",

            "crosses_per90":
                "crosses",

            "interceptions_per90":
                "interceptions",

            "tackles_won_per90":
                "tackles_won",

            "own_goals_per90":
                "own_goals",
        }

        for output, source in misc_map.items():

            value = numeric(
                group[
                    MISC_COLUMNS[source]
                ]
            ).sum(
                min_count=1
            )

            row[output] = safe_per90(
                value,
                total_minutes,
            )

        players.append(row)

    return pd.DataFrame(
        players
    )


# =============================================================================
# PCA
# =============================================================================


def fit_one_component(
    players,
    features,
    group_name,
    orientation_feature=None,
):

    X = players[
        features
    ].copy()

    observed = X.notna().sum(
        axis=1
    )

    imputed = (
        len(features)
        - observed
    )

    # Drop features with no data at all.
    usable = [
        feature
        for feature in features
        if X[feature].notna().any()
    ]

    dropped_empty = [
        feature
        for feature in features
        if feature not in usable
    ]

    if dropped_empty:

        print(
            f"{group_name}: dropping empty features:"
        )

        for feature in dropped_empty:
            print(
                f"  - {feature}"
            )

    if not usable:
        raise ValueError(
            f"{group_name}: no usable features."
        )

    X_usable = X[
        usable
    ]

    imputer = SimpleImputer(
        strategy="median"
    )

    X_imputed = imputer.fit_transform(
        X_usable
    )

    variances = np.var(
        X_imputed,
        axis=0,
    )

    keep_mask = variances > 0

    used_features = [
        feature
        for feature, keep
        in zip(
            usable,
            keep_mask,
        )
        if keep
    ]

    if not used_features:
        raise ValueError(
            f"{group_name}: all features have zero variance."
        )

    X_used = X_imputed[
        :,
        keep_mask
    ]

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(
        X_used
    )

    pca = PCA(
        n_components=1
    )

    raw_scores = pca.fit_transform(
        X_scaled
    )[:, 0]

    loadings = pca.components_[0].copy()

    if (
        orientation_feature
        and orientation_feature in used_features
    ):

        index = used_features.index(
            orientation_feature
        )

        orientation = X_scaled[
            :,
            index
        ]

    else:

        orientation = X_scaled.mean(
            axis=1
        )

    correlation = np.corrcoef(
        raw_scores,
        orientation,
    )[0, 1]

    if (
        np.isfinite(correlation)
        and correlation < 0
    ):

        raw_scores *= -1
        loadings *= -1

    std = raw_scores.std(
        ddof=0
    )

    scores = (
        np.zeros_like(raw_scores)
        if std == 0
        else (
            raw_scores
            - raw_scores.mean()
        ) / std
    )

    loading_map = dict(
        zip(
            used_features,
            loadings,
        )
    )

    rows = []

    for feature in features:

        rows.append({
            "group":
                group_name,

            "feature":
                feature,

            "loading":
                float(
                    loading_map.get(
                        feature,
                        0.0,
                    )
                ),

            "used_in_pca":
                feature in used_features,

            "observed_pct":
                float(
                    players[feature]
                    .notna()
                    .mean()
                    * 100
                ),
        })

    explained = float(
        pca.explained_variance_ratio_[0]
        * 100
    )

    loading_table = pd.DataFrame(
        rows
    )

    loading_table[
        "explained_variance_pct"
    ] = explained

    return {
        "scores":
            scores,

        "observed":
            observed,

        "imputed":
            imputed,

        "loadings":
            loading_table,

        "used_features":
            used_features,

        "explained":
            explained,
    }


# =============================================================================
# Manifest builder
# =============================================================================


def read_source_metadata(
    pca_file: Path,
):

    # First try metadata stored directly in the prepared CSV.
    try:

        head = pd.read_csv(
            pca_file,
            nrows=1,
        )

        if (
            not head.empty
            and "league" in head.columns
            and "season" in head.columns
        ):

            return (
                str(
                    head.iloc[0]["league"]
                ).strip(),
                str(
                    head.iloc[0]["season"]
                ).strip(),
            )

    except Exception:
        pass

    # Legacy prepared files may not contain league/season.
    # Try the corresponding raw source file in the same folder.
    raw_files = sorted(
        pca_file.parent.glob(
            "data_*_all_players.csv"
        )
    )

    if len(raw_files) == 1:

        try:

            raw = pd.read_csv(
                raw_files[0],
                sep=";",
                decimal=",",
                nrows=1,
            )

            if (
                not raw.empty
                and "league" in raw.columns
                and "season" in raw.columns
            ):

                return (
                    str(
                        raw.iloc[0]["league"]
                    ).strip(),
                    str(
                        raw.iloc[0]["season"]
                    ).strip(),
                )

        except Exception:
            pass

    return None


def build_visualization_manifest():

    VIZ_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Includes:
    #
    # player_pca_fbref.csv
    # player_pca_fbref_2025_26.csv
    # player_pca_fbref_2024_25.csv
    files = sorted(
        DATA_DIRECTORY.rglob(
            "player_pca_fbref*.csv"
        )
    )

    sources_by_key = {}

    for pca_file in files:

        metadata = read_source_metadata(
            pca_file
        )

        if metadata is None:

            print(
                "Manifest warning: "
                f"cannot determine league/season for {pca_file}"
            )

            continue

        league, season = metadata

        league_name = league_display_name(
            league
        )

        season_label = season_display_name(
            season
        )

        relative_path = os.path.relpath(
            pca_file,
            VIZ_DIRECTORY,
        ).replace(
            os.sep,
            "/",
        )

        key = (
            league,
            season,
        )

        source = {
            "id":
                (
                    f"{league_directory_name(league)}-"
                    f"{season_filename_token(season)}"
                ),

            "league":
                league,

            "league_name":
                league_name,

            "season":
                season,

            "season_label":
                season_label,

            "path":
                relative_path,

            "modified":
                datetime.fromtimestamp(
                    pca_file.stat().st_mtime,
                    timezone.utc,
                ).isoformat(),

            # Prefer season-specific files over legacy file.
            "_priority":
                1
                if re.search(
                    r"_\d{4}_\d{2}\.csv$",
                    pca_file.name,
                )
                else 0,
        }

        existing = sources_by_key.get(
            key
        )

        if (
            existing is None
            or source["_priority"]
            > existing["_priority"]
        ):
            sources_by_key[
                key
            ] = source

    sources = list(
        sources_by_key.values()
    )

    for source in sources:
        source.pop(
            "_priority",
            None,
        )

    sources.sort(
        key=lambda item: (
            item["league_name"].lower(),
            item["season"],
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

    print(
        f"Manifest: {MANIFEST_FILE}"
    )

    print(
        f"Found {len(sources)} PCA datasets"
    )

    for source in sources:

        print(
            "  - "
            f"{source['league_name']} "
            f"{source['season_label']}"
        )


# =============================================================================
# Main
# =============================================================================


def main():

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
        / f"data_{season_token}_all_players.csv"
    )

    output_file = (
        league_directory
        / f"player_pca_fbref_{season_token}.csv"
    )

    loadings_file = (
        league_directory
        / f"pca_loadings_fbref_{season_token}.csv"
    )

    summary_file = (
        league_directory
        / f"pca_summary_fbref_{season_token}.csv"
    )

    if not input_file.exists():

        raise FileNotFoundError(
            f"Could not find {input_file}"
        )

    print()

    print(
        "Preparing FBref PCA"
    )

    print(
        "==================="
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

    df = pd.read_csv(
        input_file,
        sep=";",
        decimal=",",
    )

    require_columns(
        df
    )

    players = combine_player_rows(
        df
    )

    if players.empty:

        raise ValueError(
            f"No players have more than "
            f"{MIN_MINUTES} minutes."
        )

    # Source metadata
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

    # -------------------------------------------------------------------------
    # PCA
    # -------------------------------------------------------------------------

    pca1 = fit_one_component(
        players,
        PCA1_FEATURES,
        "PCA1_shooting_standard",
        "shots_per90",
    )

    pca2 = fit_one_component(
        players,
        PCA2_FEATURES,
        "PCA2_team_success",
        "plus_minus_per90",
    )

    pca3 = fit_one_component(
        players,
        PCA3_FEATURES,
        "PCA3_misc_performance",
    )

    players[
        "pca1_shooting_score"
    ] = pca1["scores"]

    players[
        "pca2_team_success_score"
    ] = pca2["scores"]

    players[
        "pca3_misc_performance_score"
    ] = pca3["scores"]

    players["PC1"] = pca1["scores"]
    players["PC2"] = pca2["scores"]
    players["PC3"] = pca3["scores"]

    players[
        "pca1_observed_features"
    ] = pca1["observed"]

    players[
        "pca1_imputed_features"
    ] = pca1["imputed"]

    players[
        "pca2_observed_features"
    ] = pca2["observed"]

    players[
        "pca2_imputed_features"
    ] = pca2["imputed"]

    players[
        "pca3_observed_features"
    ] = pca3["observed"]

    players[
        "pca3_imputed_features"
    ] = pca3["imputed"]

    all_features = list(
        dict.fromkeys(
            PCA1_FEATURES
            + PCA2_FEATURES
            + PCA3_FEATURES
        )
    )

    players[
        "observed_features"
    ] = (
        players[
            all_features
        ]
        .notna()
        .sum(axis=1)
    )

    players[
        "imputed_features"
    ] = (
        len(all_features)
        - players[
            "observed_features"
        ]
    )

    output_columns = [
        "league",
        "season",
        "player",
        "team",
        "position",
        "position_group",
        "age",
        "minutes",

        "PC1",
        "PC2",
        "PC3",

        "pca1_shooting_score",
        "pca2_team_success_score",
        "pca3_misc_performance_score",

        "observed_features",
        "imputed_features",

        "pca1_observed_features",
        "pca1_imputed_features",

        "pca2_observed_features",
        "pca2_imputed_features",

        "pca3_observed_features",
        "pca3_imputed_features",

        *all_features,
    ]

    players[
        output_columns
    ].to_csv(
        output_file,
        index=False,
    )

    loadings = pd.concat(
        [
            pca1["loadings"],
            pca2["loadings"],
            pca3["loadings"],
        ],
        ignore_index=True,
    )

    loadings.to_csv(
        loadings_file,
        index=False,
    )

    summary = pd.DataFrame([
        {
            "axis":
                "PCA1",

            "group":
                "FBref Shooting Standard",

            "explained_variance_pct":
                pca1["explained"],
        },
        {
            "axis":
                "PCA2",

            "group":
                "FBref Playing Time Team Success",

            "explained_variance_pct":
                pca2["explained"],
        },
        {
            "axis":
                "PCA3",

            "group":
                "FBref Misc Performance",

            "explained_variance_pct":
                pca3["explained"],
        },
    ])

    summary.to_csv(
        summary_file,
        index=False,
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

    print()

    build_visualization_manifest()


if __name__ == "__main__":
    main()