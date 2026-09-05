import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

INPUT_FILE = Path("bundesliga_2025_26_all_players.csv")
OUTPUT_FILE = Path("player_pca.csv")
LOADINGS_FILE = Path("pca_loadings.csv")
SUMMARY_FILE = Path("pca_summary.csv")

# Strictly more than this number of minutes.
MIN_MINUTES = 400

MINUTES_COLUMN = "fbref_standard_playing_time_min"
POSITION_COLUMN = "fbref_standard_pos"
AGE_COLUMN = "fbref_standard_age"


# -----------------------------------------------------------------------------
# Feature groups
# -----------------------------------------------------------------------------
#
# The three visual axes are calculated independently:
#   X = Physical intensity PCA
#   Y = Offensive activity PCA
#   Z = Defensive activity PCA
#
# Position is NOT used in any PCA calculation. It is only used for colouring
# and filtering in the browser.
#
# All season-count features are converted to per-90 values before PCA.
# Top speed is already a maximum/rate-like value and is therefore not divided
# by minutes.

PHYSICAL_FEATURES = [
    "distance_per90",
    "sprints_per90",
    "intensive_runs_per90",
    "top_speed_kmh",
    "sprints_per_km",
    "intensive_runs_per_km",
]

OFFENSIVE_FEATURES = [
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "shots_on_target_per90",
    "crosses_per90",
    "fouls_drawn_per90",
    "offsides_per90",
    "penalty_attempts_per90",
]

DEFENSIVE_FEATURES = [
    "duels_won_per90",
    "aerial_duels_won_per90",
    "tackles_won_per90",
    "interceptions_per90",
    "fouls_committed_per90",
    "yellow_cards_per90",
]


# FBref player counts: summed across rows/clubs, then converted to per 90.
FBREF_COUNT_FEATURES = {
    # Offense
    "goals_per90": "fbref_standard_performance_gls",
    "assists_per90": "fbref_standard_performance_ast",
    "shots_per90": "fbref_shooting_standard_sh",
    "shots_on_target_per90": "fbref_shooting_standard_sot",
    "crosses_per90": "fbref_misc_performance_crs",
    "fouls_drawn_per90": "fbref_misc_performance_fld",
    "offsides_per90": "fbref_misc_performance_off",
    "penalty_attempts_per90": "fbref_standard_performance_pkatt",

    # Defense
    "tackles_won_per90": "fbref_misc_performance_tklw",
    "interceptions_per90": "fbref_misc_performance_int",
    "fouls_committed_per90": "fbref_misc_performance_fls",
    "yellow_cards_per90": "fbref_misc_performance_crdy",
}


# Bundesliga season totals. These are player-level values, so if a player has
# multiple FBref rows we take the first available value rather than summing a
# duplicated Bundesliga value across rows.
BUNDESLIGA_TOTAL_FEATURES = {
    # Physical
    "distance_per90": "bundesliga_distance_km",
    "sprints_per90": "bundesliga_sprints",
    "intensive_runs_per90": "bundesliga_intensive_runs",

    # Defense
    "duels_won_per90": "bundesliga_duels_won",
    "aerial_duels_won_per90": "bundesliga_aerial_duels_won",
}


# Bundesliga maximum / rate-like features.
BUNDESLIGA_MAX_FEATURES = {
    "top_speed_kmh": "bundesliga_top_speed_kmh",
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def first_numeric_value(series: pd.Series):
    values = numeric(series).dropna()
    if values.empty:
        return np.nan
    return values.iloc[0]


def max_numeric_value(series: pd.Series):
    values = numeric(series).dropna()
    if values.empty:
        return np.nan
    return values.max()


def classify_position(position):
    if pd.isna(position):
        return None

    primary = re.split(r"[,\s/;-]+", str(position).upper().strip())[0]

    if primary in {"GK", "G"}:
        return "GK"

    if primary in {"DF", "DEF", "D", "FB", "CB", "LB", "RB"}:
        return "DF"

    if primary in {"MF", "MID", "M", "DM", "CM", "AM", "LM", "RM", "WM"}:
        return "MF"

    if primary in {"FW", "FWD", "F", "ST", "LW", "RW"}:
        return "FW"

    return None


def require_columns(df: pd.DataFrame):
    required = {
        "player",
        "team",
        MINUTES_COLUMN,
        POSITION_COLUMN,
        AGE_COLUMN,
        *FBREF_COUNT_FEATURES.values(),
        *BUNDESLIGA_TOTAL_FEATURES.values(),
        *BUNDESLIGA_MAX_FEATURES.values(),
    }

    missing = sorted(required - set(df.columns))

    if missing:
        raise ValueError(
            "Input CSV is missing required columns:\n" +
            "\n".join(f"  - {column}" for column in missing)
        )


def combine_player_rows(df: pd.DataFrame) -> pd.DataFrame:
    players = []

    for player_name, group in df.groupby("player", sort=False):
        group = group.copy()
        group["_minutes"] = numeric(group[MINUTES_COLUMN]).fillna(0)

        total_minutes = float(group["_minutes"].sum())

        # Strictly > 400 minutes by default.
        if total_minutes <= MIN_MINUTES:
            continue

        # Use the row with the most minutes to define primary team-row metadata
        # such as position and age.
        primary_row = group.loc[group["_minutes"].idxmax()]

        teams = " / ".join(
            dict.fromkeys(
                group["team"]
                .dropna()
                .astype(str)
                .str.strip()
                .loc[lambda s: s.ne("")]
            )
        )

        raw_position = primary_row.get(POSITION_COLUMN)

        row = {
            "player": str(player_name).strip(),
            "team": teams,
            "position": "" if pd.isna(raw_position) else str(raw_position).strip(),
            "position_group": classify_position(raw_position),
            "age": pd.to_numeric(primary_row.get(AGE_COLUMN), errors="coerce"),
            "minutes": total_minutes,
        }

        # FBref counts -> sum across player/team rows -> per 90.
        for output_name, source_column in FBREF_COUNT_FEATURES.items():
            values = numeric(group[source_column])
            total = values.sum(min_count=1)

            row[output_name] = (
                float(total) * 90.0 / total_minutes
                if pd.notna(total)
                else np.nan
            )

        # Bundesliga player totals -> first available -> per 90.
        for output_name, source_column in BUNDESLIGA_TOTAL_FEATURES.items():
            value = first_numeric_value(group[source_column])

            row[output_name] = (
                float(value) * 90.0 / total_minutes
                if pd.notna(value)
                else np.nan
            )

        # Rate/maximum features are not normalized to 90.
        for output_name, source_column in BUNDESLIGA_MAX_FEATURES.items():
            row[output_name] = max_numeric_value(group[source_column])

        # Intensity relative to total distance.
        distance_total = first_numeric_value(group["bundesliga_distance_km"])
        sprints_total = first_numeric_value(group["bundesliga_sprints"])
        intensive_total = first_numeric_value(group["bundesliga_intensive_runs"])

        row["sprints_per_km"] = (
            float(sprints_total) / float(distance_total)
            if pd.notna(sprints_total)
            and pd.notna(distance_total)
            and float(distance_total) > 0
            else np.nan
        )

        row["intensive_runs_per_km"] = (
            float(intensive_total) / float(distance_total)
            if pd.notna(intensive_total)
            and pd.notna(distance_total)
            and float(distance_total) > 0
            else np.nan
        )

        players.append(row)

    return pd.DataFrame(players)


def fit_one_component(
    players: pd.DataFrame,
    feature_names: list[str],
    group_name: str,
):
    """
    Fit one PCA component for one semantic feature group.

    Missing values are median-imputed. Every feature is z-standardized before
    PCA. The component sign is then oriented so that larger scores correspond,
    on average, to larger values across the group's standardized metrics.

    Finally the component score itself is standardized to mean 0 / SD 1. This
    makes the three visual axes easier to compare.
    """

    X = players[feature_names].copy()

    # Keep visibility of missing-data quality in the exported CSV.
    observed_count = X.notna().sum(axis=1)
    imputed_count = len(feature_names) - observed_count

    # Guard against accidental entirely-empty features.
    entirely_missing = [
        feature for feature in feature_names
        if X[feature].notna().sum() == 0
    ]

    if entirely_missing:
        raise ValueError(
            f"{group_name}: these selected PCA features contain no data at all: "
            + ", ".join(entirely_missing)
        )

    imputer = SimpleImputer(strategy="median")
    X_imputed = imputer.fit_transform(X)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)

    pca = PCA(n_components=1)
    raw_scores = pca.fit_transform(X_scaled)[:, 0]
    loadings = pca.components_[0].copy()

    # PCA signs are arbitrary. Orient the component so positive means "more"
    # of the overall group profile rather than the inverse.
    mean_feature_activity = X_scaled.mean(axis=1)
    correlation = np.corrcoef(raw_scores, mean_feature_activity)[0, 1]

    if np.isfinite(correlation) and correlation < 0:
        raw_scores *= -1
        loadings *= -1

    # Standardize the final component score so 0 is league-average and +/-1
    # is approximately one standard deviation along this grouped PCA axis.
    score_std = raw_scores.std(ddof=0)

    if score_std == 0:
        scores = np.zeros_like(raw_scores)
    else:
        scores = (raw_scores - raw_scores.mean()) / score_std

    loading_table = pd.DataFrame({
        "group": group_name,
        "feature": feature_names,
        "loading": loadings,
        "observed_pct": [players[f].notna().mean() * 100 for f in feature_names],
        "imputation_median": imputer.statistics_,
    })

    explained_variance_pct = float(pca.explained_variance_ratio_[0] * 100)
    loading_table["explained_variance_pct"] = explained_variance_pct

    return {
        "scores": scores,
        "observed_count": observed_count,
        "imputed_count": imputed_count,
        "loadings": loading_table,
        "explained_variance_pct": explained_variance_pct,
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}. Put it in the same folder as this script."
        )

    # Current project CSV format: semicolon delimiter and decimal comma.
    df = pd.read_csv(INPUT_FILE, sep=";", decimal=",")
    require_columns(df)

    players = combine_player_rows(df)

    if players.empty:
        raise ValueError(
            f"No players have more than {MIN_MINUTES} total minutes."
        )

    if players["position_group"].isna().any():
        unknown = players.loc[
            players["position_group"].isna(),
            ["player", "position"]
        ]
        print("Warning: unclassified positions found:")
        print(unknown.to_string(index=False))

    physical = fit_one_component(players, PHYSICAL_FEATURES, "physical")
    offensive = fit_one_component(players, OFFENSIVE_FEATURES, "offensive")
    defensive = fit_one_component(players, DEFENSIVE_FEATURES, "defensive")

    players["physical_score"] = physical["scores"]
    players["offensive_score"] = offensive["scores"]
    players["defensive_score"] = defensive["scores"]

    players["physical_observed_features"] = physical["observed_count"]
    players["physical_imputed_features"] = physical["imputed_count"]

    players["offensive_observed_features"] = offensive["observed_count"]
    players["offensive_imputed_features"] = offensive["imputed_count"]

    players["defensive_observed_features"] = defensive["observed_count"]
    players["defensive_imputed_features"] = defensive["imputed_count"]

    # Keep a backwards-friendly total quality count too.
    all_pca_features = list(dict.fromkeys(
        PHYSICAL_FEATURES + OFFENSIVE_FEATURES + DEFENSIVE_FEATURES
    ))
    players["observed_features"] = players[all_pca_features].notna().sum(axis=1)
    players["imputed_features"] = len(all_pca_features) - players["observed_features"]

    output_columns = [
        "player",
        "team",
        "position",
        "position_group",
        "age",
        "minutes",
        "physical_score",
        "offensive_score",
        "defensive_score",
        "observed_features",
        "imputed_features",
        "physical_observed_features",
        "physical_imputed_features",
        "offensive_observed_features",
        "offensive_imputed_features",
        "defensive_observed_features",
        "defensive_imputed_features",
        *all_pca_features,
    ]

    players[output_columns].to_csv(OUTPUT_FILE, index=False)

    loadings = pd.concat(
        [
            physical["loadings"],
            offensive["loadings"],
            defensive["loadings"],
        ],
        ignore_index=True,
    )
    loadings.to_csv(LOADINGS_FILE, index=False)

    summary = pd.DataFrame([
        {
            "axis": "Physical intensity",
            "score_column": "physical_score",
            "feature_count": len(PHYSICAL_FEATURES),
            "explained_variance_pct": physical["explained_variance_pct"],
        },
        {
            "axis": "Offensive activity",
            "score_column": "offensive_score",
            "feature_count": len(OFFENSIVE_FEATURES),
            "explained_variance_pct": offensive["explained_variance_pct"],
        },
        {
            "axis": "Defensive activity",
            "score_column": "defensive_score",
            "feature_count": len(DEFENSIVE_FEATURES),
            "explained_variance_pct": defensive["explained_variance_pct"],
        },
    ])
    summary.to_csv(SUMMARY_FILE, index=False)

    print()
    print("Grouped PCA complete")
    print("====================")
    print(f"Input rows:              {len(df)}")
    print(f"Players > {MIN_MINUTES} min:      {len(players)}")
    print()
    print("Axis variance captured inside each feature group:")
    print(f"  Physical intensity: {physical['explained_variance_pct']:.1f}%")
    print(f"  Offensive activity: {offensive['explained_variance_pct']:.1f}%")
    print(f"  Defensive activity: {defensive['explained_variance_pct']:.1f}%")
    print()
    print("Position counts:")
    print(players["position_group"].value_counts(dropna=False).to_string())
    print()
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Saved: {LOADINGS_FILE}")
    print(f"Saved: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
