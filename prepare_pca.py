import re

import numpy as np
import pandas as pd

from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


INPUT_FILE = "bundesliga_2025_26_all_players.csv"
OUTPUT_FILE = "player_pca.csv"
LOADINGS_FILE = "pca_loadings.csv"

MIN_MINUTES = 400


# ---------------------------------------------------------
# Columns
# ---------------------------------------------------------

MINUTES_COLUMN = "fbref_standard_playing_time_min"

# FBref event counts.
# These are summed if a player played for multiple clubs.
FBREF_COUNT_FEATURES = {
    "tackles_won_per90": "fbref_misc_performance_tklw",
    "interceptions_per90": "fbref_misc_performance_int",
    "fouls_committed_per90": "fbref_misc_performance_fls",
    "fouls_drawn_per90": "fbref_misc_performance_fld",
    "crosses_per90": "fbref_misc_performance_crs",
}

# Bundesliga season totals.
# These are converted to per-90 values.
BUNDESLIGA_TOTAL_FEATURES = {
    "distance_per90": "bundesliga_distance_km",
    "sprints_per90": "bundesliga_sprints",
    "intensive_runs_per90": "bundesliga_intensive_runs",
    "duels_won_per90": "bundesliga_duels_won",
    "aerial_duels_won_per90": "bundesliga_aerial_duels_won",
}

# Already a rate/maximum, so DON'T normalize to 90.
BUNDESLIGA_RATE_FEATURES = {
    "top_speed_kmh": "bundesliga_top_speed_kmh",
}


def first_numeric_value(series):
    """Return first available numeric value, otherwise NaN."""
    values = pd.to_numeric(series, errors="coerce").dropna()

    if len(values) == 0:
        return np.nan

    return values.iloc[0]


def classify_position(position):
    """Convert FBref position to GK / DF / MF / FW."""

    if pd.isna(position):
        return None

    primary = re.split(
        r"[,\s/;-]+",
        str(position).upper().strip()
    )[0]

    if primary == "GK":
        return "GK"

    if primary in ["DF", "DEF", "FB", "CB", "LB", "RB"]:
        return "DF"

    if primary in ["MF", "MID", "DM", "CM", "AM", "LM", "RM", "WM"]:
        return "MF"

    if primary in ["FW", "FWD", "ST", "LW", "RW"]:
        return "FW"

    return None


# ---------------------------------------------------------
# Load CSV
# ---------------------------------------------------------

# Your CSV uses semicolon separators and decimal commas.
df = pd.read_csv(
    INPUT_FILE,
    sep=";",
    decimal=","
)


# ---------------------------------------------------------
# Collapse multiple club rows into one player
# ---------------------------------------------------------

players = []

for player_name, group in df.groupby("player", sort=False):

    group = group.copy()

    group["_minutes"] = pd.to_numeric(
        group[MINUTES_COLUMN],
        errors="coerce"
    ).fillna(0)

    total_minutes = group["_minutes"].sum()

    if total_minutes <= MIN_MINUTES:
        continue

    # Use the club row with the most minutes for primary position.
    primary_row = group.loc[group["_minutes"].idxmax()]

    teams = " / ".join(
        dict.fromkeys(
            group["team"]
            .dropna()
            .astype(str)
        )
    )

    raw_position = primary_row["fbref_standard_pos"]

    row = {
        "player": player_name,
        "team": teams,
        "position": raw_position,
        "position_group": classify_position(raw_position),
        "age": pd.to_numeric(
            primary_row["fbref_standard_age"],
            errors="coerce"
        ),
        "minutes": total_minutes,
    }

    # -----------------------------------------------------
    # FBref counts → sum across teams → per 90
    # -----------------------------------------------------

    for output_name, source_column in FBREF_COUNT_FEATURES.items():

        values = pd.to_numeric(
            group[source_column],
            errors="coerce"
        )

        total = values.sum(min_count=1)

        if pd.notna(total):
            row[output_name] = total * 90 / total_minutes
        else:
            row[output_name] = np.nan

    # -----------------------------------------------------
    # Bundesliga season totals → per 90
    # -----------------------------------------------------

    for output_name, source_column in BUNDESLIGA_TOTAL_FEATURES.items():

        value = first_numeric_value(
            group[source_column]
        )

        if pd.notna(value):
            row[output_name] = value * 90 / total_minutes
        else:
            row[output_name] = np.nan

    # -----------------------------------------------------
    # Bundesliga rates / maxima
    # -----------------------------------------------------

    for output_name, source_column in BUNDESLIGA_RATE_FEATURES.items():

        row[output_name] = first_numeric_value(
            group[source_column]
        )

    players.append(row)


players = pd.DataFrame(players)


# ---------------------------------------------------------
# PCA feature matrix
# ---------------------------------------------------------

FEATURES = [
    "distance_per90",
    "sprints_per90",
    "intensive_runs_per90",
    "duels_won_per90",
    "aerial_duels_won_per90",
    "tackles_won_per90",
    "interceptions_per90",
    "fouls_committed_per90",
    "fouls_drawn_per90",
    "crosses_per90",
    "top_speed_kmh",
]

X = players[FEATURES].copy()


# ---------------------------------------------------------
# Track how much data was originally available
# ---------------------------------------------------------

players["observed_features"] = X.notna().sum(axis=1)

players["imputed_features"] = (
    len(FEATURES) -
    players["observed_features"]
)


# ---------------------------------------------------------
# Missing values
# ---------------------------------------------------------

# PCA cannot operate with NaN.
#
# Median imputation is used globally.
# IMPORTANT:
# position is NOT used for imputation.
#
# Therefore we don't artificially make defenders look
# like defenders, etc.

imputer = SimpleImputer(strategy="median")

X_imputed = imputer.fit_transform(X)


# ---------------------------------------------------------
# Standardization
# ---------------------------------------------------------

# Essential before PCA because:
#
# distance ≈ 10
# top speed ≈ 30
# tackles ≈ 1
#
# should not differ in importance simply because
# their numerical scales differ.

scaler = StandardScaler()

X_scaled = scaler.fit_transform(
    X_imputed
)


# ---------------------------------------------------------
# PCA
# ---------------------------------------------------------

pca = PCA(n_components=3)

coordinates = pca.fit_transform(
    X_scaled
)

players["PC1"] = coordinates[:, 0]
players["PC2"] = coordinates[:, 1]
players["PC3"] = coordinates[:, 2]


# ---------------------------------------------------------
# Save PCA loadings
# ---------------------------------------------------------

loadings = pd.DataFrame(
    pca.components_.T,
    index=FEATURES,
    columns=[
        "PC1",
        "PC2",
        "PC3"
    ]
)

loadings.index.name = "feature"

loadings.to_csv(
    LOADINGS_FILE
)


# ---------------------------------------------------------
# Save visualization data
# ---------------------------------------------------------

output_columns = [
    "player",
    "team",
    "position",
    "position_group",
    "age",
    "minutes",

    "PC1",
    "PC2",
    "PC3",

    "observed_features",
    "imputed_features",
] + FEATURES


players[output_columns].to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# Report
# ---------------------------------------------------------

print()
print("PCA complete")
print("------------")

print(
    f"Players: {len(players)}"
)

print()

for i, variance in enumerate(
    pca.explained_variance_ratio_,
    start=1
):
    print(
        f"PC{i}: {variance * 100:.1f}%"
    )

print(
    f"PC1-PC3 total: "
    f"{pca.explained_variance_ratio_.sum() * 100:.1f}%"
)

print()

print("PCA loadings:")
print(
    loadings.round(3)
)

print()

print(
    f"Saved {OUTPUT_FILE}"
)

print(
    f"Saved {LOADINGS_FILE}"
)