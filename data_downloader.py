#!/usr/bin/env python3
"""
Bundesliga 2025/26 player-statistics downloader.

Purpose
-------
Create one large player-level CSV for the 2025/26 Bundesliga season.

Source priority
---------------
1. FBref is the primary source.
   If a statistic is available and populated on FBref, use the FBref value.

2. Bundesliga.com is the fallback/additional source.
   Only use Bundesliga.com for statistics that are not available/populated on
   FBref, especially physical/tracking metrics such as:
       - distance covered
       - top speed
       - sprints
       - intensive runs
       - duels won
       - aerial duels won
       - successful passes from open play (%)
       - crosses from open play
       - shots against post/bar

Output
------
When run, this script creates:

    bundesliga_2025_26_all_players.csv

It does NOT create the CSV merely by being imported.

Recommended installation
------------------------
    python -m pip install pandas numpy soccerdata playwright rapidfuzz Unidecode lxml html5lib
    python -m playwright install chromium

Run
---
    python data_downloader.py
"""

from __future__ import annotations

import re
import sys
import time
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import soccerdata as sd
from playwright.sync_api import sync_playwright
from playwright.sync_api import expect, TimeoutError as PlaywrightTimeoutError
from rapidfuzz import fuzz, process
from unidecode import unidecode


SEASON = "2025-2026"
FBREF_LEAGUE = "GER-Bundesliga"
OUTPUT_FILE = Path("bundesliga_2025_26_all_players.csv")

# FBref tables that still contain useful populated player-season data for 25/26.
FBREF_STAT_TYPES = [
    "standard",
    "shooting",
    "playing_time",
    "misc",
    "keeper",
]

# Bundesliga-only/fallback statistics.
#
# Important:
# We deliberately do not duplicate statistics such as goals or assists here
# because FBref is the preferred source whenever that information exists there.
BUNDESLIGA_STATS = {
    "shots_against_post_bar": {
        "slug": "shots-against-post",
        "title": "Shots against post and bar",
    },
    "pass_success_open_play_pct": {
        "slug": "passes",
        "title": "Successful passes from open play (%)",
    },
    "duels_won": {
        "slug": "duels-won",
        "title": "Duels won",
    },
    "aerial_duels_won": {
        "slug": "aerial-duels-won",
        "title": "Aerial duels won",
    },
    "crosses_open_play": {
        "slug": "crosses",
        "title": "Crosses from open play",
    },
    "distance_km": {
        "slug": "distance",
        "title": "Distance covered (km)",
    },
    "top_speed_kmh": {
        "slug": "top-speed",
        "title": "Top speed (km/h)",
    },
    "sprints": {
        "slug": "sprints",
        "title": "Sprints",
    },
    "intensive_runs": {
        "slug": "intensive-runs",
        "title": "Intensive runs",
    },
}


def clean_token(value: object) -> str:
    """Convert one column-label part into a stable snake_case token."""
    text = str(value).strip()

    if not text or text.lower() == "nan" or text.startswith("Unnamed:"):
        return ""

    text = unidecode(text)
    text = text.replace("+/-", "plus_minus")
    text = text.replace("%", "pct")
    text = text.replace("+", " plus ")
    text = text.replace("/", " per ")
    text = text.replace("-", " ")

    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text)

    return text.strip("_").lower()


def flatten_fbref_columns(df: pd.DataFrame, stat_type: str) -> pd.DataFrame:
    """
    Flatten FBref/soccerdata MultiIndex columns.

    Identifier columns stay readable:
        league, season, team, player

    Every statistic receives an explicit source/table prefix such as:
        fbref_standard_playing_time_min
        fbref_shooting_standard_sh
        fbref_misc_performance_fls

    This makes provenance clear and prevents accidental collisions.
    """
    df = df.copy()

    flattened: List[str] = []

    for col in df.columns:
        parts = list(col) if isinstance(col, tuple) else [col]
        tokens = [clean_token(p) for p in parts]
        tokens = [t for t in tokens if t]

        key = next(
            (
                t
                for t in tokens
                if t in {"league", "season", "team", "player"}
            ),
            None,
        )

        if key:
            flattened.append(key)
            continue

        suffix = "_".join(tokens) if tokens else "value"
        flattened.append(
            f"fbref_{clean_token(stat_type)}_{suffix}"
        )

    # Guarantee unique column names.
    seen: Dict[str, int] = {}
    unique: List[str] = []

    for name in flattened:
        count = seen.get(name, 0)
        seen[name] = count + 1

        if count == 0:
            unique.append(name)
        else:
            unique.append(f"{name}_{count + 1}")

    df.columns = unique
    return df


def get_fbref_data() -> pd.DataFrame:
    """
    Download and merge all useful FBref player-season tables.

    FBref is treated as the authoritative primary source.
    """
    print("Downloading FBref player-season tables...")

    fbref = sd.FBref(
        leagues=FBREF_LEAGUE,
        seasons=SEASON,
    )

    key_cols = ["league", "season", "team", "player"]
    merged: Optional[pd.DataFrame] = None

    for stat_type in FBREF_STAT_TYPES:
        print(f"  FBref: {stat_type}")

        raw = fbref.read_player_season_stats(
            stat_type=stat_type
        )

        frame = flatten_fbref_columns(
            raw.reset_index(),
            stat_type,
        )

        missing_keys = [
            key for key in key_cols
            if key not in frame.columns
        ]

        if missing_keys:
            raise RuntimeError(
                f"FBref '{stat_type}' table is missing expected "
                f"identifier columns: {missing_keys}"
            )

        frame = frame.drop_duplicates(
            subset=key_cols,
            keep="first",
        )

        if merged is None:
            merged = frame
        else:
            merged = merged.merge(
                frame,
                on=key_cols,
                how="outer",
                validate="one_to_one",
            )

        # Be polite to FBref and avoid bursts if the cache is empty.
        time.sleep(6.5)

    if merged is None or merged.empty:
        raise RuntimeError(
            "FBref returned no player data."
        )

    merged = (
        merged
        .sort_values(["team", "player"], kind="stable")
        .reset_index(drop=True)
    )

    print(f"  FBref players/rows: {len(merged):,}")
    return merged


def normalize_player_name(name: object) -> str:
    """
    Normalize names only for cross-site joining.

    The original player spelling remains untouched in the final output.
    """
    text = unidecode(str(name)).lower()
    text = text.replace("ß", "ss")
    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
        flags=re.UNICODE,
    )
    text = re.sub(
        r"\b(jr|junior|sr|senior)\b",
        " ",
        text,
    )
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def parse_number(text: object) -> float:
    """Convert text such as '36.74 km/h' or '91,3 %' to a float."""
    text = str(text).strip().replace(",", ".")
    text = re.sub(r"[^0-9.+-]", "", text)

    if (
        not text
        or text in {"+", "-", ".", "+.", "-."}
    ):
        return np.nan

    try:
        return float(text)
    except ValueError:
        return np.nan


def extract_table_from_html(
    html: str,
) -> Optional[pd.DataFrame]:
    """
    Try to read a conventional HTML table from Bundesliga.com.

    This is the preferred scraper path because it is less dependent on
    page-layout details.
    """
    try:
        tables = pd.read_html(StringIO(html))
    except ValueError:
        return None

    for table in tables:
        if len(table) < 5 or table.shape[1] < 2:
            continue

        cols = [str(c).lower() for c in table.columns]

        player_idx = next(
            (
                i
                for i, col in enumerate(cols)
                if "player" in col or "spieler" in col
            ),
            None,
        )

        if player_idx is None:
            continue

        value_idx = None

        # Prefer a numeric column near the right side.
        for i in reversed(range(table.shape[1])):
            if i == player_idx:
                continue

            numeric = pd.to_numeric(
                table.iloc[:, i]
                .astype(str)
                .str.replace(",", ".", regex=False),
                errors="coerce",
            )

            if numeric.notna().sum() >= max(
                3,
                len(table) // 3,
            ):
                value_idx = i
                break

        if value_idx is None:
            continue

        out = pd.DataFrame(
            {
                "bundesliga_player":
                    table.iloc[:, player_idx]
                    .astype(str)
                    .str.strip(),
                "value":
                    table.iloc[:, value_idx]
                    .map(parse_number),
            }
        )

        out = out[
            out["bundesliga_player"].ne("")
            & out["bundesliga_player"].ne("nan")
            & out["value"].notna()
        ]

        if len(out) >= 5:
            return out.drop_duplicates(
                "bundesliga_player",
                keep="first",
            )

    return None


def extract_leaderboard_with_js(
    page,
    title: str,
) -> pd.DataFrame:
    """
    Fallback DOM parser for Bundesliga.com's ranking component.

    The website is dynamic, so this parser finds the active statistic heading,
    then searches its nearby ranking container for player links and numeric
    values.
    """
    rows = page.evaluate(
        """
        ({title}) => {
          const norm = s =>
            (s || "").replace(/\\s+/g, " ").trim().toLowerCase();

          const target = norm(title);

          const headings = [
            ...document.querySelectorAll(
              "h1,h2,h3,h4,h5,h6,[role='heading']"
            )
          ];

          let heading = headings.find(h => {
            const t = norm(
              h.innerText || h.textContent
            );
            return (
              t === target
              || t.includes(target)
            );
          });

          if (!heading) {
            const all = [
              ...document.querySelectorAll("body *")
            ];

            heading = all.find(
              el =>
                norm(
                  el.innerText || el.textContent
                ) === target
            );
          }

          if (!heading) {
            return [];
          }

          let node = heading;
          let container = null;

          for (
            let i = 0;
            i < 10 && node;
            i++, node = node.parentElement
          ) {
            const links = node.querySelectorAll(
              "a[href*='/player/'], a[href*='/spieler/']"
            ).length;

            if (links >= 5) {
              container = node;

              if (links >= 10) {
                break;
              }
            }
          }

          if (!container) {
            return [];
          }

          // The leader is a card; subsequent entries are links that ARE rows.
          // Read dedicated fields so ranks, headings and values cannot become names.
          const structuredRows = [
            ...container.querySelectorAll('.card-stats, a.playerRow')
          ].map(row => ({
            player: (row.querySelector('.card-stats__name, .playerName')?.textContent || '').trim(),
            value: (row.querySelector('.card-stats__value, .value')?.textContent || '').trim()
          })).filter(row => row.player && row.value);
          if (structuredRows.length) {
            return structuredRows;
          }

          const links = [
            ...container.querySelectorAll(
              "a[href*='/player/'], a[href*='/spieler/']"
            )
          ];

          const out = [];
          const used = new Set();

          for (const a of links) {
            let name = (
              a.innerText
              || a.textContent
              || a.getAttribute("aria-label")
              || a.getAttribute("title")
              || ""
            )
            .replace(/\\s+/g, " ")
            .trim();

            if (
              !name
              || name.length < 2
              || used.has(name)
            ) {
              continue;
            }

            let row = a;
            let chosen = null;

            for (
              let i = 0;
              i < 7
                && row
                && row !== container;
              i++, row = row.parentElement
            ) {
              const playerLinks =
                row.querySelectorAll(
                  "a[href*='/player/'], a[href*='/spieler/']"
                ).length;

              const text = (
                row.innerText
                || row.textContent
                || ""
              )
              .replace(/\\s+/g, " ")
              .trim();

              if (
                playerLinks === 1
                && /\\d/.test(text)
              ) {
                chosen = row;
                break;
              }
            }

            if (!chosen) {
              continue;
            }

            const text = (
              chosen.innerText
              || chosen.textContent
              || ""
            )
            .replace(/\\s+/g, " ")
            .trim();

            const nums =
              text.match(
                /[+-]?\\d+(?:[.,]\\d+)?/g
              ) || [];

            if (!nums.length) {
              continue;
            }

            // Rankings usually show rank first and statistic last.
            const value =
              nums[nums.length - 1];

            used.add(name);

            out.push({
              player: name,
              value: value
            });
          }

          return out;
        }
        """,
        {"title": title},
    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "bundesliga_player",
                "value",
            ]
        )

    out = (
        pd.DataFrame(rows)
        .rename(
            columns={
                "player":
                    "bundesliga_player"
            }
        )
    )

    out["bundesliga_player"] = (
        out["bundesliga_player"]
        .astype(str)
        .str.strip()
    )

    out["value"] = out["value"].map(
        parse_number
    )

    out = out[
        out["bundesliga_player"].ne("")
        & out["value"].notna()
    ]

    return out.drop_duplicates(
        "bundesliga_player",
        keep="first",
    )


def dismiss_contentpass(page) -> None:
    """Wait for the asynchronously loaded consent frame when present."""
    try:
        page.frame_locator('iframe[title="Contentpass First Layer"]').get_by_role(
            "button", name=re.compile(r"agree.*continue", re.I)
        ).click(timeout=5_000)
    except PlaywrightTimeoutError:
        pass


def click_load_more(
    page,
    max_clicks: int = 80,
) -> None:
    """Expand a Bundesliga.com ranking as far as possible."""
    for _ in range(max_clicks):
        buttons = page.get_by_text(
            re.compile(
                r"^\s*Load more\s*$",
                re.I,
            )
        )

        try:
            count = buttons.count()
        except Exception:
            count = 0

        if count == 0:
            break

        button = buttons.first

        try:
            if not button.is_visible():
                break

            # Loading also disables this button briefly. Wait before deciding
            # that a disabled button means the leaderboard is complete.
            try:
                expect(button).to_be_enabled(timeout=10_000)
            except AssertionError:
                break

            previous_count = page.locator("a.playerRow").count()
            button.scroll_into_view_if_needed()
            try:
                button.click(timeout=4_000)
            except PlaywrightTimeoutError:
                dismiss_contentpass(page)
                button.click(timeout=4_000)
            try:
                page.wait_for_function(
                    "count => document.querySelectorAll('a.playerRow').length > count",
                    arg=previous_count,
                    timeout=15_000,
                )
            except PlaywrightTimeoutError:
                if not button.is_enabled():
                    break
                raise

        except Exception as exc:
            raise RuntimeError(
                "Could not expand the Bundesliga ranking; refusing to save a partial leaderboard. "
                f"{exc}"
            ) from exc
    else:
        raise RuntimeError("Bundesliga ranking exceeded the Load more safety limit.")


def scrape_bundesliga_stat(
    page,
    slug: str,
    title: str,
) -> pd.DataFrame:
    """Download one 2025/26 Bundesliga.com player ranking."""
    url = (
        "https://www.bundesliga.com/"
        f"en/bundesliga/stats/players/{slug}/{SEASON}"
    )

    print(f"  Bundesliga.com: {title}")

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    page.wait_for_timeout(1_500)

    # The consent overlay can live in a separate Contentpass iframe.
    dismiss_contentpass(page)

    # Cookie dialogs differ by location/site revision.
    for pattern in [
        r"accept all",
        r"accept",
        r"agree",
        r"allow all",
    ]:
        try:
            btn = page.get_by_role(
                "button",
                name=re.compile(
                    pattern,
                    re.I,
                ),
            )

            if (
                btn.count()
                and btn.first.is_visible()
            ):
                btn.first.click(
                    timeout=1_500
                )
                page.wait_for_timeout(300)
                break

        except Exception:
            pass

    click_load_more(page)

    html = page.content()

    table = extract_table_from_html(
        html
    )

    if table is None or len(table) < 10:
        table = extract_leaderboard_with_js(
            page,
            title,
        )

    if table.empty:
        raise RuntimeError(
            f"Could not extract Bundesliga.com "
            f"leaderboard '{title}' from {url}. "
            "The website structure may have changed."
        )

    print(
        f"    extracted {len(table):,} players"
    )

    return table


def get_bundesliga_only_data() -> pd.DataFrame:
    """
    Download statistics used only as fallback/additional fields.

    These are intentionally kept separate from FBref so duplicate football
    statistics do not overwrite FBref values.
    """
    print(
        "Downloading Bundesliga.com-only statistics..."
    )

    merged: Optional[pd.DataFrame] = None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 "
                "(X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/126 Safari/537.36"
            ),
        )

        page = context.new_page()

        for out_name, config in BUNDESLIGA_STATS.items():
            frame = scrape_bundesliga_stat(
                page,
                slug=config["slug"],
                title=config["title"],
            )

            value_col = (
                f"bundesliga_{out_name}"
            )

            frame = frame.rename(
                columns={
                    "value": value_col
                }
            )

            frame["join_name"] = (
                frame["bundesliga_player"]
                .map(normalize_player_name)
            )

            frame = (
                frame[
                    [
                        "join_name",
                        "bundesliga_player",
                        value_col,
                    ]
                ]
                .drop_duplicates(
                    "join_name",
                    keep="first",
                )
            )

            if merged is None:
                merged = frame
            else:
                merged = merged.merge(
                    frame,
                    on="join_name",
                    how="outer",
                    validate="one_to_one",
                    suffixes=("", "_new"),
                )
                merged["bundesliga_player"] = merged["bundesliga_player"].combine_first(
                    merged.pop("bundesliga_player_new")
                )

            page.wait_for_timeout(500)

        context.close()
        browser.close()

    if merged is None:
        return pd.DataFrame(
            columns=["join_name"]
        )

    return merged


def attach_bundesliga_stats(
    fbref: pd.DataFrame,
    bundesliga: pd.DataFrame,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Attach Bundesliga.com-only statistics to FBref player rows.

    Matching strategy:
    1. normalized exact name match
    2. conservative fuzzy match
    3. otherwise leave unmatched

    The script prefers missing values over a risky/wrong player match.
    """
    out = fbref.copy()

    out["join_name"] = (
        out["player"]
        .map(normalize_player_name)
    )

    duplicate_keys = set(
        out.loc[
            out["join_name"]
            .duplicated(keep=False),
            "join_name",
        ]
    )

    unique_fbref = (
        out.loc[
            ~out["join_name"]
            .isin(duplicate_keys),
            ["join_name", "player"],
        ]
        .drop_duplicates("join_name")
    )

    candidate_keys = (
        unique_fbref["join_name"]
        .tolist()
    )

    candidate_set = set(
        candidate_keys
    )

    mapping: Dict[str, str] = {}
    unmatched: List[str] = []

    for _, row in bundesliga.iterrows():
        source_key = row["join_name"]

        source_name = row.get(
            "bundesliga_player",
            source_key,
        )

        if source_key in candidate_set:
            mapping[source_key] = source_key
            continue

        matches = process.extract(
            source_key,
            candidate_keys,
            scorer=fuzz.ratio,
            limit=2,
        )

        if not matches:
            unmatched.append(
                str(source_name)
            )
            continue

        best_name, best_score, _ = (
            matches[0]
        )

        second_score = (
            matches[1][1]
            if len(matches) > 1
            else 0
        )

        if (
            best_score >= 92
            and (
                best_score - second_score
            ) >= 4
        ):
            mapping[source_key] = (
                best_name
            )
        else:
            unmatched.append(
                str(source_name)
            )

    b = bundesliga.copy()

    b["join_name"] = (
        b["join_name"]
        .map(
            lambda x:
                mapping.get(x)
        )
    )

    b = b[
        b["join_name"].notna()
    ].copy()

    if "bundesliga_player" in b.columns:
        b = b.drop(
            columns=[
                "bundesliga_player"
            ]
        )

    out = out.merge(
        b,
        on="join_name",
        how="left",
        validate="many_to_one",
    )

    out = out.drop(
        columns=["join_name"]
    )

    identifiers = [
        col
        for col in [
            "player",
            "team",
            "season",
            "league",
        ]
        if col in out.columns
    ]

    bundesliga_cols = sorted(
        col
        for col in out.columns
        if col.startswith(
            "bundesliga_"
        )
    )

    fbref_cols = [
        col
        for col in out.columns
        if col not in identifiers
        and col not in bundesliga_cols
    ]

    out = out[
        identifiers
        + fbref_cols
        + bundesliga_cols
    ]

    return (
        out,
        sorted(set(unmatched)),
    )


def main() -> int:
    """Run the complete downloader and write the merged CSV."""
    try:
        fbref = get_fbref_data()

        bundesliga = (
            get_bundesliga_only_data()
        )

        final, unmatched = (
            attach_bundesliga_stats(
                fbref,
                bundesliga,
            )
        )

        final.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig",
        )

        print()
        print(
            f"Saved: "
            f"{OUTPUT_FILE.resolve()}"
        )
        print(
            f"Players/rows: "
            f"{len(final):,}"
        )
        print(
            f"Columns: "
            f"{len(final.columns):,}"
        )

        if unmatched:
            print()
            print(
                "Bundesliga.com player names "
                "not matched automatically:"
            )

            for name in unmatched:
                print(f"  - {name}")

            print()
            print(
                "These values were left "
                "unmatched rather than risk "
                "merging statistics into the "
                "wrong player."
            )

        return 0

    except Exception as exc:
        print(
            f"\nERROR: {exc}",
            file=sys.stderr,
        )

        print(
            "\nIf Bundesliga.com scraping "
            "fails, first make sure Chromium "
            "is installed:\n"
            "    python -m playwright install chromium\n",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
