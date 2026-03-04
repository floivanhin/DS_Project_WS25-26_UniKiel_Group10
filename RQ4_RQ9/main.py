from __future__ import annotations

"""Bundesliga 2024/25 analysis pipeline.

Goal:
- Report team- and league-level age metrics.
- Answer RQ4: Which players perform better at home vs away?
- Answer RQ9: How is team age related to efficiency (goals per shot)?

Approach:
- Load and cache player data via ESPN/soccerdata.
- Aggregate WhoScored events for RQ4.
- Aggregate ESPN match summaries for RQ9 on team and match level.
- Save outputs as clearly separated CSV groups: `core`, `rq4`, `rq9`.
"""

import argparse
import importlib
import json
import os
import subprocess
import sys
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Iterator


STARTUP_PACKAGES = {
    "pandas": "pandas",
    "requests": "requests",
}

_DEPENDENCY_STATUS: dict[str, bool] = {}


def ensure_package(import_name: str, package_name: str) -> bool:
    """Ensure that a package can be imported.

    What happens:
    - Reuse a cached result from `_DEPENDENCY_STATUS` when available.
    - Try a direct import.
    - If missing, run `pip install` automatically when possible.
    - Import again to verify installation succeeded.

    Why:
    - This makes startup robust for beginners by detecting and fixing
      missing base packages immediately.
    """
    # Fast path: reuse known status to avoid repeated import/install attempts.
    if import_name in _DEPENDENCY_STATUS:
        return _DEPENDENCY_STATUS[import_name]

    try:
        # Default case: package is already available.
        importlib.import_module(import_name)
        _DEPENDENCY_STATUS[import_name] = True
        return True
    except ImportError:
        print(f"[setup] Package '{package_name}' is missing. Starting installation ...")

    if import_name == "soccerdata" and sys.version_info >= (3, 14):
        # Important special case: soccerdata relies on binary dependencies
        # (for example lxml) that may not be available on very new Python versions.
        print(
            "[setup] soccerdata is currently incompatible with Python "
            f"{sys.version_info.major}.{sys.version_info.minor} "
            "(typically requires Python 3.12 or 3.13 because of lxml binary wheels)."
        )
        _DEPENDENCY_STATUS[import_name] = False
        return False

    try:
        # Install using the exact interpreter that runs this script.
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
    except subprocess.CalledProcessError:
        _DEPENDENCY_STATUS[import_name] = False
        return False

    try:
        # Final verification: package counts as available only if import now works.
        importlib.import_module(import_name)
        _DEPENDENCY_STATUS[import_name] = True
        return True
    except ImportError:
        _DEPENDENCY_STATUS[import_name] = False
        return False


# Startup check for essential libraries before running the pipeline.
for _import_name, _package_name in STARTUP_PACKAGES.items():
    if not ensure_package(_import_name, _package_name):
        raise RuntimeError(
            f"Automatic installation of '{_package_name}' failed."
        )

import pandas as pd
import numpy as np


TARGET_SEASON = "2425"
DEFAULT_SEASONS = [TARGET_SEASON]
DEFAULT_LEAGUE = "GER-Bundesliga"
DEFAULT_SOURCE_PRIORITY = ["espn"]
RQ4_MIN_MATCHES_FOR_LEADERBOARD = 5
RQ4_MIN_MATCHES_PER_SIDE_FOR_DELTA = 5
ESPN_MATCH_SUMMARY_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/summary?event={game_id}"
)
ESPN_ATHLETE_URL = "https://site.web.api.espn.com/apis/common/v3/sports/soccer/athletes/{athlete_id}"


@dataclass
class Config:
    seasons: list[str]
    league: str
    soccerdata_cache_dir: Path
    player_cache_dir: Path
    output_dir: Path
    refresh: bool
    no_cache: bool
    no_store: bool
    proxy: str | None
    source_priority: list[str]


@dataclass
class CoreOutputs:
    """Core outputs for age analysis without RQ-specific logic."""

    player_table: pd.DataFrame
    team_summary: pd.DataFrame
    season_summary: pd.DataFrame
    global_summary: pd.DataFrame


@dataclass
class RQ4Outputs:
    """Outputs for RQ4 (home/away performance)."""

    summary: pd.DataFrame
    delta: pd.DataFrame


@dataclass
class RQ9Outputs:
    """Outputs for RQ9 (age vs efficiency)."""

    summary: pd.DataFrame
    match_efficiency: pd.DataFrame
    peak_summary: pd.DataFrame
    player_age_profile: pd.DataFrame
    player_best_age: pd.DataFrame


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments and set practical defaults.

    Why:
    - Keeps runs reproducible with explicit options
      (cache, proxy, season, output folder, source priority).
    """
    parser = argparse.ArgumentParser(
        description=(
            "Computes average age of Bundesliga players per team and season "
            "(fixed to 2024/25)."
        )
    )
    parser.add_argument(
        "--seasons",
        nargs="+",
        default=DEFAULT_SEASONS,
        help="Season code for soccerdata (only 2425 is supported).",
    )
    parser.add_argument(
        "--league",
        default=DEFAULT_LEAGUE,
        help="League code for soccerdata (default: GER-Bundesliga).",
    )
    parser.add_argument(
        "--soccerdata-cache-dir",
        default="./.soccerdata_cache",
        help="Cache directory for soccerdata.",
    )
    parser.add_argument(
        "--player-cache-dir",
        default="./data/player_cache",
        help="Custom cache directory for season player lists.",
    )
    parser.add_argument(
        "--output-dir",
        default="./data/outputs",
        help="Output directory for CSV files.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore existing season player caches and fetch fresh data.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Set SOCCERDATA_NOCACHE=true.",
    )
    parser.add_argument(
        "--no-store",
        action="store_true",
        help="Set SOCCERDATA_NOSTORE=true.",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Optional proxy for soccerdata, e.g. socks5://127.0.0.1:9050.",
    )
    parser.add_argument(
        "--source-priority",
        nargs="+",
        default=DEFAULT_SOURCE_PRIORITY,
        help="Data source priority order (only espn is supported).",
    )
    return parser.parse_args(argv)


def configure_env(config: Config) -> None:
    """Prepare directories and environment variables for data loading."""
    # Existing directories are fine (`exist_ok=True`), missing ones are created.
    config.soccerdata_cache_dir.mkdir(parents=True, exist_ok=True)
    config.player_cache_dir.mkdir(parents=True, exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # soccerdata reads these environment variables internally.
    os.environ["SOCCERDATA_DIR"] = str(config.soccerdata_cache_dir.resolve())
    os.environ.setdefault("SOCCERDATA_LOGLEVEL", "INFO")
    if config.no_cache:
        os.environ["SOCCERDATA_NOCACHE"] = "true"
    if config.no_store:
        os.environ["SOCCERDATA_NOSTORE"] = "true"


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names (MultiIndex -> simple snake_case names)."""
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        cols: list[str] = []
        for col in out.columns:
            # Remove empty pieces and join levels with "_"
            # so later column access is unambiguous.
            pieces = [str(p).strip() for p in col if p and str(p).strip()]
            cols.append("_".join(pieces) if pieces else "col")
        out.columns = cols
    # Unified naming simplifies merges/filters and reduces typo risk.
    out.columns = [str(c).strip().lower().replace(" ", "_") for c in out.columns]
    return out


def parse_age_to_float(value: object) -> float:
    """Normalize age values to `float`.

    Supports:
    - numeric input
    - regular strings like "24.5"
    - ESPN-like format "YY-DDD" (years-days)
    """
    if pd.isna(value):
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return float("nan")

    if "-" in text:
        # Some sources provide age as "YY-DDD" (years-days).
        try:
            years, days = text.split("-", 1)
            return int(years) + int(days) / 365.25
        except (TypeError, ValueError):
            return float("nan")

    try:
        return float(text)
    except ValueError:
        return float("nan")


def parse_espn_display_dob(value: object) -> date | None:
    """Parse ESPN date-of-birth values from multiple common date formats."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    if "T" in text:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def age_years_at_reference_date(birth_date: date, reference_date: date) -> float:
    """Compute age in years at a fixed reference date."""
    return (reference_date - birth_date).days / 365.25


def parse_season_years(season_code: str) -> tuple[int, int] | None:
    """Derive season start/end year from a season code (e.g. 2425 -> 2024/2025)."""
    code = str(season_code).strip()
    if len(code) != 4 or not code.isdigit():
        return None

    left = int(code[:2])
    right = int(code[2:])
    if right == (left + 1) % 100:
        start = 2000 + left
        end = 2000 + right
        if end <= start:
            end += 100
        return start, end

    full_year = int(code)
    if 1900 <= full_year <= 2100:
        return full_year, full_year + 1
    return None


def normalize_season_label(season_code: str) -> str:
    """Create a readable season label for reports/CSV (e.g. 2024/2025)."""
    years = parse_season_years(season_code)
    if years is None:
        return str(season_code).strip()
    start, end = years
    return f"{start}/{end}"


def season_reference_date(season_code: str) -> date:
    """Define age reference date per season (default: June 30 in end year)."""
    years = parse_season_years(season_code)
    if years is not None:
        _, end = years
        return date(end, 6, 30)
    return date.today()


def cache_file_for_season(cache_dir: Path, league: str, season: str) -> Path:
    """Build the file path for the season player cache."""
    safe_league = league.replace("/", "_").replace(" ", "_")
    return cache_dir / f"{safe_league}_{season}_players.csv"


def whoscored_rating_cache_file_for_season(
    cache_dir: Path, league: str, season: str
) -> Path:
    """Build the file path for the season WhoScored rating cache."""
    safe_league = league.replace("/", "_").replace(" ", "_")
    return cache_dir / f"{safe_league}_{season}_whoscored_ratings.csv"


def build_requests_proxies(proxy: str | None) -> dict[str, str] | None:
    """Build Requests proxy dict for HTTP/HTTPS or `None` without proxy."""
    if not proxy:
        return None
    return {"http": proxy, "https": proxy}


def load_json_from_cache_or_url(
    url: str,
    cache_file: Path,
    refresh: bool,
    proxy: str | None = None,
    timeout: int = 30,
) -> dict:
    """Read JSON from local cache or fetch it from URL.

    Why:
    - Reduces API calls and speeds up repeated runs.
    - `refresh=True` lets you intentionally overwrite cache content.
    """
    # Read local cache first if present and no forced refresh is requested.
    if cache_file.exists() and not refresh:
        with cache_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    import requests

    # Fallback: call API if no valid cache can be used.
    response = requests.get(
        url,
        timeout=timeout,
        proxies=build_requests_proxies(proxy),
    )
    response.raise_for_status()
    payload = response.json()
    # Cache the response immediately for faster, reproducible future runs.
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return payload


def should_log_progress(current: int, total: int, interval: int) -> bool:
    """Control when progress is logged (start, end, interval points)."""
    if total <= 0:
        return True
    return current == 1 or current == total or (current % max(1, interval) == 0)


def format_progress(label: str, current: int, total: int) -> str:
    """Build a compact text progress bar."""
    if total <= 0:
        return f"[progress] {label}: [{'#' * 24}] 0/0 (100.0%, remaining=0)"
    safe_current = max(0, min(int(current), int(total)))
    percent = (safe_current / total) * 100
    remaining = max(0, int(total) - safe_current)
    bar_width = 24
    filled = int(round((safe_current / total) * bar_width))
    bar = "#" * filled + "-" * (bar_width - filled)
    return (
        f"[progress] {label}: [{bar}] {safe_current}/{total} "
        f"({percent:.1f}%, remaining={remaining})"
    )


def load_players_from_espn(config: Config, season: str, sd_module) -> pd.DataFrame:
    """Load players, teams, and age information from ESPN.

    Flow:
    1. Load schedule.
    2. Read match summaries for each match (cache-first).
    3. Extract team rosters per match.
    4. Collect unique players and load profiles (DOB/age).
    5. Compute player age at the season reference date.
    6. Return a cleaned DataFrame.
    """
    # `soccerdata.ESPN` is the primary interface for schedule and event data.
    espn = sd_module.ESPN(
        leagues=config.league,
        seasons=[season],
        no_cache=config.no_cache,
        no_store=config.no_store,
        proxy=config.proxy,
    )
    schedule = espn.read_schedule().reset_index()
    if schedule.empty:
        raise RuntimeError(f"No ESPN schedule data found for season {season}.")

    # Safety check: without game_id/league_id we cannot build summary URLs.
    required_cols = {"game_id", "league_id"}
    missing_schedule_cols = [c for c in required_cols if c not in schedule.columns]
    if missing_schedule_cols:
        raise RuntimeError(
            f"ESPN schedule is missing expected columns: "
            f"{', '.join(missing_schedule_cols)}"
        )

    summary_cache_dir = config.player_cache_dir / "_espn_match_summaries" / str(season)
    roster_rows: list[dict] = []
    total_matches = len(schedule)
    summary_cache_hits = 0
    summary_downloads = 0
    summary_expected_downloads = (
        total_matches
        if config.refresh
        else int(
            sum(
                1
                for _, match in schedule.iterrows()
                if not (summary_cache_dir / f"{str(match['game_id'])}.json").exists()
            )
        )
    )
    summary_poll_left = summary_expected_downloads
    summary_interval = max(1, total_matches // 20)
    print(
        f"[info] ESPN season {season}: processing {total_matches} matches "
        "(match summaries). "
        f"Expected polls: {summary_expected_downloads}."
    )
    for idx, (_, match) in enumerate(schedule.iterrows(), start=1):
        # Build match summary API URL and cache file path for each match.
        game_id = str(match["game_id"])
        league_id = str(match["league_id"])
        url = ESPN_MATCH_SUMMARY_URL.format(league_id=league_id, game_id=game_id)
        cache_file = summary_cache_dir / f"{game_id}.json"
        from_cache = cache_file.exists() and not config.refresh
        data = load_json_from_cache_or_url(
            url=url,
            cache_file=cache_file,
            refresh=config.refresh,
            proxy=config.proxy,
        )
        if from_cache:
            summary_cache_hits += 1
        else:
            summary_downloads += 1
            summary_poll_left = max(0, summary_poll_left - 1)
        if should_log_progress(idx, total_matches, summary_interval):
            print(
                (
                    f"{format_progress('Match-Summaries', idx, total_matches)} | "
                    f"cache={summary_cache_hits}, polled={summary_downloads}, "
                    f"poll_left={summary_poll_left}"
                ),
                flush=True,
            )

        # Flatten roster structure from match summary into row records.
        for team_data in data.get("rosters", []):
            team_name = (
                team_data.get("team", {}).get("displayName")
                or team_data.get("team", {}).get("name")
            )
            if not team_name:
                continue
            for player_data in team_data.get("roster", []):
                athlete = player_data.get("athlete", {})
                player_id = str(athlete.get("id") or "").strip()
                player_name = (
                    athlete.get("displayName") or athlete.get("fullName") or ""
                ).strip()
                if not player_id or not player_name:
                    continue
                roster_rows.append(
                    {
                        "league": config.league,
                        "season": str(season),
                        "team": team_name,
                        "player": player_name,
                        "player_id": player_id,
                        "game_id": game_id,
                    }
                )

    if not roster_rows:
        raise RuntimeError(f"No ESPN roster data found for season {season}.")

    # Consolidate repeated player-match rows into player-season view.
    roster_df = pd.DataFrame.from_records(roster_rows)
    players = (
        roster_df.groupby(
            ["league", "season", "team", "player", "player_id"], dropna=False
        )
        .agg(appearances=("game_id", "nunique"))
        .reset_index()
    )

    athlete_cache_dir = config.player_cache_dir / "_espn_athletes"
    athlete_profiles: list[dict] = []
    unique_player_ids = sorted(players["player_id"].dropna().astype(str).unique())
    total_athletes = len(unique_player_ids)
    athlete_cache_hits = 0
    athlete_downloads = 0
    athlete_expected_downloads = (
        total_athletes
        if config.refresh
        else int(
            sum(
                1
                for player_id in unique_player_ids
                if not (athlete_cache_dir / f"{player_id}.json").exists()
            )
        )
    )
    athlete_poll_left = athlete_expected_downloads
    athlete_interval = max(1, total_athletes // 20)
    print(
        f"[info] ESPN season {season}: processing {total_athletes} player profiles "
        f"(Athlete API). Expected polls: {athlete_expected_downloads}."
    )
    for idx, player_id in enumerate(unique_player_ids, start=1):
        # Optionally load a dedicated profile per player with DOB/age.
        athlete_url = ESPN_ATHLETE_URL.format(athlete_id=player_id)
        athlete_cache_file = athlete_cache_dir / f"{player_id}.json"
        from_cache = athlete_cache_file.exists() and not config.refresh
        try:
            athlete_payload = load_json_from_cache_or_url(
                url=athlete_url,
                cache_file=athlete_cache_file,
                refresh=config.refresh,
                proxy=config.proxy,
            )
        except Exception:
            athlete_profiles.append(
                {"player_id": player_id, "display_dob": None, "age_current": None}
            )
        else:
            athlete_data = athlete_payload.get("athlete", {})
            athlete_profiles.append(
                {
                    "player_id": player_id,
                    "display_dob": athlete_data.get("displayDOB"),
                    "age_current": athlete_data.get("age"),
                }
            )
        if from_cache:
            athlete_cache_hits += 1
        else:
            athlete_downloads += 1
            athlete_poll_left = max(0, athlete_poll_left - 1)
        if should_log_progress(idx, total_athletes, athlete_interval):
            print(
                (
                    f"{format_progress('Player profiles', idx, total_athletes)} | "
                    f"cache={athlete_cache_hits}, polled={athlete_downloads}, "
                    f"poll_left={athlete_poll_left}"
                ),
                flush=True,
            )

    athlete_df = pd.DataFrame.from_records(athlete_profiles)
    # Join roster data (who played) with profile data (how old).
    players = players.merge(athlete_df, how="left", on="player_id")

    # Compute age at a fixed season reference date to keep players comparable
    # within the same season.
    reference_date = season_reference_date(season)
    birth_dates = players["display_dob"].apply(parse_espn_display_dob)
    players["age_ref"] = birth_dates.apply(
        lambda b: age_years_at_reference_date(b, reference_date)
        if isinstance(b, date)
        else float("nan")
    )
    # Fallback: if DOB is missing, use ESPN's current age value.
    players["age_ref"] = players["age_ref"].fillna(
        pd.to_numeric(players["age_current"], errors="coerce")
    )
    players["age"] = players["age_ref"].round(2)
    players["season_label"] = players["season"].apply(normalize_season_label)
    players["data_source"] = "ESPN"

    keep_cols = [
        "league",
        "season",
        "season_label",
        "team",
        "player",
        "player_id",
        "appearances",
        "age",
        "age_ref",
        "data_source",
    ]
    # Return only the required and stable columns.
    return players[keep_cols].copy()


def load_or_fetch_players_for_season(config: Config, season: str) -> pd.DataFrame:
    """Return player data for one season with cache and fallback logic.

    Why this structure:
    - Check cache first (fast and reproducible).
    - Try data sources in configured priority order.
    - Continue to next source if one source fails.
    """
    # Check/import soccerdata lazily so errors can include helpful version hints.
    if not ensure_package("soccerdata", "soccerdata"):
        pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
        raise RuntimeError(
            "Package 'soccerdata' is missing or could not be installed automatically. "
            f"Current Python version: {pyver}. "
            "Please install with a compatible Python version "
            "(recommended 3.12/3.13): pip install soccerdata pandas"
        )
    import soccerdata as sd

    cache_file = cache_file_for_season(config.player_cache_dir, config.league, season)
    # Use existing season cache first if available.
    if cache_file.exists() and not config.refresh:
        cached_df = pd.read_csv(cache_file)
        if "age_ref" not in cached_df.columns and "age" in cached_df.columns:
            cached_df["age_ref"] = cached_df["age"].apply(parse_age_to_float)
        # Old caches may contain invalid age values; filter them out.
        cached_age = pd.to_numeric(cached_df.get("age_ref"), errors="coerce")
        if cached_age.notna().any() and float(cached_age.median()) > 80:
            print(
                f"[warn] Dropping outdated cache for season {season} "
                "(implausible age values detected)."
            )
        else:
            print(
                f"[info] Season {season}: using existing player cache "
                "(poll_left=0)."
            )
            return cached_df

    # Source pipeline: currently only ESPN, but structure is extensible.
    source_loaders = {"espn": load_players_from_espn}
    source_errors: list[str] = []
    final_df: pd.DataFrame | None = None
    total_sources = len(config.source_priority)
    if total_sources > 0:
        print(format_progress(f"Data sources season {season}", 0, total_sources))
    for source_idx, source in enumerate(config.source_priority, start=1):
        loader = source_loaders[source]
        print(f"[info] Trying data source '{source.upper()}' for season {season} ...")
        try:
            final_df = loader(config, season, sd)
            print(f"[ok] Data source '{source.upper()}' succeeded for season {season}.")
            print(format_progress(f"Data sources season {season}", source_idx, total_sources))
            break
        except Exception as exc:
            print(
                f"[warn] Data source '{source.upper()}' failed "
                f"({type(exc).__name__}): {exc}"
            )
            source_errors.append(f"{source.upper()}: {exc}")
            print(format_progress(f"Data sources season {season}", source_idx, total_sources))

    if final_df is None:
        raise RuntimeError(
            f"All data sources failed for season {season}: "
            + " | ".join(source_errors)
        )

    # Cache successful output for future runs without API load.
    final_df.to_csv(cache_file, index=False)
    return final_df


def load_or_fetch_whoscored_ratings_for_season(
    config: Config, season: str, sd_module
) -> pd.DataFrame:
    """Read WhoScored player data for RQ4, preferring local cache.

    Output:
    - one row per player per match with overall rating and home/away flag.
    """
    cache_cols = [
        "season",
        "season_label",
        "game_id",
        "game",
        "team",
        "home_away",
        "player",
        "player_id",
        "overall_rating",
        "is_starting_xi",
        "is_man_of_the_match",
    ]
    cache_file = whoscored_rating_cache_file_for_season(
        config.player_cache_dir, config.league, season
    )
    # Reuse existing rating cache if it has all expected columns.
    if cache_file.exists() and not config.refresh:
        cached_df = pd.read_csv(cache_file)
        missing_cols = [c for c in cache_cols if c not in cached_df.columns]
        if not missing_cols:
            return cached_df[cache_cols].copy()
        print(
            f"[warn] Dropping incomplete WhoScored cache for season {season}: "
            + ", ".join(missing_cols)
        )

    whoscored = sd_module.WhoScored(
        leagues=config.league,
        seasons=[season],
        no_cache=config.no_cache,
        no_store=config.no_store,
        proxy=config.proxy,
    )
    print(f"[info] WhoScored season {season}: loading schedule ...")
    schedule = whoscored.read_schedule(force_cache=not config.refresh).reset_index()
    if schedule.empty:
        return pd.DataFrame(columns=cache_cols)
    # Without these key fields, events cannot be resolved reliably.
    required_schedule_cols = {"game_id", "home_team", "away_team"}
    missing_schedule_cols = [c for c in required_schedule_cols if c not in schedule.columns]
    if missing_schedule_cols:
        raise RuntimeError(
            "WhoScored schedule is missing expected columns: "
            + ", ".join(missing_schedule_cols)
        )
    schedule["game_id"] = schedule["game_id"].apply(_parse_int)
    schedule = schedule.dropna(subset=["game_id"]).copy()
    if schedule.empty:
        return pd.DataFrame(columns=cache_cols)
    schedule["game_id"] = schedule["game_id"].astype(int)
    schedule["season"] = schedule["season"].astype(str)

    # soccerdata stores event JSON files in this directory layout.
    league_key = (
        str(schedule.iloc[0]["league"]).strip() if "league" in schedule.columns else config.league
    )
    events_dir = (
        config.soccerdata_cache_dir
        / "data"
        / "WhoScored"
        / "events"
        / f"{league_key}_{season}"
    )
    game_ids = sorted(schedule["game_id"].dropna().astype(int).unique())
    existing_ids = {gid for gid in game_ids if (events_dir / f"{gid}.json").exists()}
    ids_to_fetch = game_ids if config.refresh else [gid for gid in game_ids if gid not in existing_ids]
    print(
        f"[info] WhoScored season {season}: matches={len(game_ids)}, "
        f"cache={len(existing_ids)}, download={len(ids_to_fetch)}"
    )
    download_total = len(ids_to_fetch)
    download_done = 0
    if ids_to_fetch:
        print(
            f"{format_progress('WhoScored-Download', download_done, download_total)} | "
            f"poll_left={max(0, download_total - download_done)}",
            flush=True,
        )
        whoscored.read_events(
            match_id=ids_to_fetch,
            force_cache=not config.refresh,
            output_fmt=None,
            on_error="skip",
        )
        download_done = download_total
        print(
            f"{format_progress('WhoScored-Download', download_done, download_total)} | "
            f"poll_left={max(0, download_total - download_done)}",
            flush=True,
        )
    else:
        print(
            f"[info] WhoScored season {season}: no polling needed, using cache only."
        )

    # Index match metadata so event parsing can access it quickly.
    meta = schedule.drop_duplicates(subset=["game_id"], keep="first").set_index("game_id")
    rows: list[dict] = []
    total_games = len(game_ids)
    interval = max(1, total_games // 20)
    files_used = 0
    for idx, game_id in enumerate(game_ids, start=1):
        event_file = events_dir / f"{game_id}.json"
        if not event_file.exists():
            continue
        files_used += 1
        with event_file.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        game_meta = meta.loc[game_id]
        home_team = _fix_mojibake(str(game_meta.get("home_team") or "").strip())
        away_team = _fix_mojibake(str(game_meta.get("away_team") or "").strip())
        game_label = str(game_meta.get("game") or "").strip()
        for side in ("home", "away"):
            side_data = payload.get(side, {})
            if not isinstance(side_data, dict):
                continue
            team_name = _fix_mojibake(str(side_data.get("name") or "").strip())
            if not team_name:
                team_name = home_team if side == "home" else away_team
            players = side_data.get("players", [])
            if not isinstance(players, list):
                continue
            for player_data in players:
                if not isinstance(player_data, dict):
                    continue
                player_id = str(player_data.get("playerId") or "").strip()
                player_name = _fix_mojibake(str(player_data.get("name") or "").strip())
                # The ratings dict usually contains minute-by-minute values.
                # We use the last value as the match's final rating.
                overall_rating = extract_whoscored_overall_rating(player_data)
                if not player_id or not player_name or overall_rating is None:
                    continue
                rows.append(
                    {
                        "season": str(season),
                        "season_label": normalize_season_label(str(season)),
                        "game_id": str(game_id),
                        "game": game_label,
                        "team": team_name,
                        "home_away": side,
                        "player": player_name,
                        "player_id": player_id,
                        "overall_rating": float(overall_rating),
                        "is_starting_xi": bool(player_data.get("isFirstEleven")),
                        "is_man_of_the_match": bool(player_data.get("isManOfTheMatch")),
                    }
                )
        if should_log_progress(idx, total_games, interval):
            print(
                (
                    f"{format_progress('WhoScored-Matches', idx, total_games)} | "
                    f"parsed={files_used}, poll_left={max(0, download_total - download_done)}"
                ),
                flush=True,
            )

    if not rows:
        return pd.DataFrame(columns=cache_cols)
    out_df = pd.DataFrame.from_records(rows)
    out_df = out_df.sort_values(
        ["season", "home_away", "overall_rating", "player"],
        ascending=[True, True, False, True],
        kind="stable",
    )
    # Persistent cache for later RQ4 runs without reparsing.
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(cache_file, index=False)
    return out_df[cache_cols].copy()


def compute_rq4_home_away_player_ratings(config: Config) -> pd.DataFrame:
    """RQ4: Aggregate WhoScored ratings by player, split by home/away."""
    if not ensure_package("soccerdata", "soccerdata"):
        print("[warn] RQ4: package 'soccerdata' is not available.")
        return empty_rq4_home_away_summary()

    import soccerdata as sd

    season_frames: list[pd.DataFrame] = []
    total_seasons = len(config.seasons)
    if total_seasons > 0:
        print(format_progress("RQ4 seasons", 0, total_seasons), flush=True)
    for idx, season in enumerate(config.seasons, start=1):
        # Load each season separately so failures remain isolated per season.
        print(f"[info] RQ4: processing season {season} ...")
        try:
            season_df = load_or_fetch_whoscored_ratings_for_season(config, season, sd)
        except Exception as exc:
            print(
                f"[warn] RQ4: WhoScored fetch failed for season {season} "
                f"({type(exc).__name__}): {exc}"
            )
        else:
            if not season_df.empty:
                season_frames.append(season_df)
        finally:
            print(format_progress("RQ4 seasons", idx, total_seasons), flush=True)

    if not season_frames:
        return empty_rq4_home_away_summary()
    match_df = pd.concat(season_frames, ignore_index=True)
    if match_df.empty:
        return empty_rq4_home_away_summary()
    # Normalize numeric/boolean columns so aggregations are reliable.
    match_df["overall_rating"] = pd.to_numeric(match_df["overall_rating"], errors="coerce")
    match_df = match_df.dropna(subset=["overall_rating"])
    if match_df.empty:
        return empty_rq4_home_away_summary()
    match_df["is_starting_xi"] = match_df["is_starting_xi"].apply(_to_bool)
    match_df["is_man_of_the_match"] = match_df["is_man_of_the_match"].apply(_to_bool)

    rq4 = (
        match_df.groupby(
            ["season", "season_label", "home_away", "player", "player_id"], dropna=False
        )
        .agg(
            matches=("game_id", "nunique"),
            teams=("team", lambda s: int(pd.Series(s).dropna().nunique())),
            avg_overall_rating=("overall_rating", "mean"),
            median_overall_rating=("overall_rating", "median"),
            best_overall_rating=("overall_rating", "max"),
            worst_overall_rating=("overall_rating", "min"),
            starts=("is_starting_xi", lambda s: int(pd.Series(s).sum())),
            motm_awards=("is_man_of_the_match", lambda s: int(pd.Series(s).sum())),
        )
        .reset_index()
    )
    # Flag rows eligible for later leaderboards with minimum match count.
    rq4["eligible_for_leaderboard"] = (
        pd.to_numeric(rq4["matches"], errors="coerce").fillna(0).astype(int)
        >= RQ4_MIN_MATCHES_FOR_LEADERBOARD
    )
    rq4 = rq4.sort_values(
        ["season", "home_away", "avg_overall_rating", "matches", "player"],
        ascending=[True, True, False, False, True],
        kind="stable",
    )
    return rq4


def compute_rq4_home_away_delta(rq4_summary: pd.DataFrame) -> pd.DataFrame:
    """RQ4: Build direct home-vs-away deltas per player from side view."""
    columns = [
        "season",
        "season_label",
        "player",
        "player_id",
        "home_matches",
        "away_matches",
        "matches_total",
        "home_avg_overall_rating",
        "away_avg_overall_rating",
        "avg_rating_delta_home_minus_away",
        "abs_avg_rating_delta",
        "home_median_overall_rating",
        "away_median_overall_rating",
        "home_best_overall_rating",
        "away_best_overall_rating",
        "home_worst_overall_rating",
        "away_worst_overall_rating",
        "home_starts",
        "away_starts",
        "home_motm_awards",
        "away_motm_awards",
        "home_teams",
        "away_teams",
        "eligible_both_sides",
    ]
    if rq4_summary.empty:
        return pd.DataFrame(columns=columns)

    side_df = rq4_summary.copy()
    side_df["home_away"] = side_df["home_away"].astype(str).str.strip().str.lower()
    side_df = side_df[side_df["home_away"].isin({"home", "away"})].copy()
    if side_df.empty:
        return pd.DataFrame(columns=columns)

    keys = ["season", "season_label", "player", "player_id"]
    metrics = [
        "matches",
        "avg_overall_rating",
        "median_overall_rating",
        "best_overall_rating",
        "worst_overall_rating",
        "starts",
        "motm_awards",
        "teams",
    ]

    def _prep_side(side: str) -> pd.DataFrame:
        # Side-specific columns get prefixes (`home_`/`away_`)
        # so names stay unique after merge.
        frame = side_df[side_df["home_away"] == side][keys + metrics].copy()
        frame = frame.rename(columns={c: f"{side}_{c}" for c in metrics})
        return frame

    home = _prep_side("home")
    away = _prep_side("away")
    merged = home.merge(away, how="outer", on=keys)

    int_cols = [
        "home_matches",
        "away_matches",
        "home_starts",
        "away_starts",
        "home_motm_awards",
        "away_motm_awards",
        "home_teams",
        "away_teams",
    ]
    float_cols = [
        "home_avg_overall_rating",
        "away_avg_overall_rating",
        "home_median_overall_rating",
        "away_median_overall_rating",
        "home_best_overall_rating",
        "away_best_overall_rating",
        "home_worst_overall_rating",
        "away_worst_overall_rating",
    ]
    for col in int_cols:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce").astype("Int64")
    for col in float_cols:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce")

    # Core RQ4 metric: how large is the home-vs-away performance gap per player?
    merged["matches_total"] = (
        pd.to_numeric(merged["home_matches"], errors="coerce").fillna(0)
        + pd.to_numeric(merged["away_matches"], errors="coerce").fillna(0)
    ).astype("Int64")
    merged["avg_rating_delta_home_minus_away"] = (
        merged["home_avg_overall_rating"] - merged["away_avg_overall_rating"]
    )
    merged["abs_avg_rating_delta"] = merged["avg_rating_delta_home_minus_away"].abs()
    merged["eligible_both_sides"] = (
        pd.to_numeric(merged["home_matches"], errors="coerce").fillna(0).astype(int)
        >= RQ4_MIN_MATCHES_PER_SIDE_FOR_DELTA
    ) & (
        pd.to_numeric(merged["away_matches"], errors="coerce").fillna(0).astype(int)
        >= RQ4_MIN_MATCHES_PER_SIDE_FOR_DELTA
    )

    merged = merged.sort_values(
        ["season", "abs_avg_rating_delta", "matches_total", "player"],
        ascending=[True, False, False, True],
        kind="stable",
    )
    return merged[columns].copy()


def compute_rq4_outputs(config: Config) -> RQ4Outputs:
    """Compute all RQ4 tables (summary + home/away delta)."""
    # Build side summary first, then derive the delta table.
    summary = compute_rq4_home_away_player_ratings(config)
    delta = compute_rq4_home_away_delta(summary)
    return RQ4Outputs(summary=summary, delta=delta)


def compute_team_player_table(players_df: pd.DataFrame) -> pd.DataFrame:
    """Create flat base table `season-team-player-age`."""
    table = players_df[["season", "season_label", "team", "player", "age_ref"]].copy()
    table = table.sort_values(["season", "team", "player"], kind="stable")
    return table


def compute_team_summary(players_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate age statistics per team and season."""
    grouped = (
        players_df.groupby(["season", "season_label", "team"], dropna=False)
        .agg(
            player_count=("player", "nunique"),
            avg_age=("age_ref", "mean"),
            min_age=("age_ref", "min"),
            max_age=("age_ref", "max"),
            missing_age=("age_ref", lambda s: int(s.isna().sum())),
        )
        .reset_index()
    )
    grouped = grouped.sort_values(
        ["season", "avg_age", "team"], ascending=[True, False, True], kind="stable"
    )
    return grouped


def deduplicate_for_league_view(players_df: pd.DataFrame) -> pd.DataFrame:
    """Remove team duplicates per player/season for league-level analysis.

    Why:
    - A player can appear for multiple teams in the same season.
    - For league-level metrics we want to count each player once.
    """
    dedup = players_df.copy()
    minute_col = None
    for candidate in ("playing_time_min", "minutes", "appearances"):
        if candidate in dedup.columns:
            minute_col = candidate
            break
    if minute_col:
        # If playtime/appearances are available, keep the row
        # with the largest usage footprint.
        dedup[minute_col] = pd.to_numeric(dedup[minute_col], errors="coerce").fillna(-1)
        dedup = dedup.sort_values(
            ["season", "player", minute_col],
            ascending=[True, True, False],
            kind="stable",
        )
    else:
        dedup = dedup.sort_values(["season", "player"], kind="stable")
    dedup = dedup.drop_duplicates(subset=["season", "player"], keep="first")
    return dedup


def compute_season_and_global_summary(
    players_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute season-level and global summaries for age metrics."""
    dedup = deduplicate_for_league_view(players_df)
    season_summary = (
        dedup.groupby(["season", "season_label"], dropna=False)
        .agg(
            unique_players=("player", "nunique"),
            avg_age=("age_ref", "mean"),
            min_age=("age_ref", "min"),
            max_age=("age_ref", "max"),
            missing_age=("age_ref", lambda s: int(s.isna().sum())),
        )
        .reset_index()
        .sort_values(["season"], kind="stable")
    )

    global_summary = pd.DataFrame(
        [
            {
                # View 1: all team entries (a player can appear multiple times).
                "scope": "all_team_entries",
                "unique_players": int(players_df["player"].nunique()),
                "avg_age": players_df["age_ref"].mean(),
                "min_age": players_df["age_ref"].min(),
                "max_age": players_df["age_ref"].max(),
                "missing_age": int(players_df["age_ref"].isna().sum()),
            },
            {
                # View 2: deduplicated per player/season (fairer league view).
                "scope": "dedup_per_player_and_season",
                "unique_players": int(dedup["player"].nunique()),
                "avg_age": dedup["age_ref"].mean(),
                "min_age": dedup["age_ref"].min(),
                "max_age": dedup["age_ref"].max(),
                "missing_age": int(dedup["age_ref"].isna().sum()),
            },
        ]
    )
    return season_summary, global_summary


def load_players_for_config(config: Config) -> pd.DataFrame:
    """Load all configured seasons and return one combined player DataFrame."""
    season_frames: list[pd.DataFrame] = []
    total_seasons = len(config.seasons)
    if total_seasons > 0:
        print(format_progress("Total seasons", 0, total_seasons))
    for idx, season in enumerate(config.seasons, start=1):
        # Load season by season, then concatenate into one full dataset.
        print(f"[info] Loading season {season} ...")
        season_frames.append(load_or_fetch_players_for_season(config, season))
        print(format_progress("Total seasons", idx, total_seasons))
    return pd.concat(season_frames, ignore_index=True)


def compute_core_outputs(players_df: pd.DataFrame) -> CoreOutputs:
    """Prepare the non-RQ-specific core of the age analysis."""
    # Core data is the shared foundation for report, RQ4, and RQ9.
    player_table = compute_team_player_table(players_df)
    team_summary = compute_team_summary(players_df)
    season_summary, global_summary = compute_season_and_global_summary(players_df)
    return CoreOutputs(
        player_table=player_table,
        team_summary=team_summary,
        season_summary=season_summary,
        global_summary=global_summary,
    )


def _parse_float(value: object) -> float | None:
    """Helper parser: convert robust inputs to `float` or `None`."""
    try:
        if value is None or pd.isna(value):
            return None
    except TypeError:
        if value is None:
            return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_bool(value: object) -> bool:
    """Helper parser for boolean flags from heterogeneous API values."""
    if isinstance(value, bool):
        return value
    try:
        if value is None or pd.isna(value):
            return False
    except TypeError:
        if value is None:
            return False
    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return True
    if text in {"0", "false", "f", "no", "n", ""}:
        return False
    numeric = _parse_float(text)
    if numeric is not None:
        return not math.isclose(numeric, 0.0, abs_tol=1e-12)
    return False


def extract_whoscored_overall_rating(player_data: dict) -> float | None:
    """Extract the final overall rating from WhoScored player data."""
    stats = player_data.get("stats", {})
    if not isinstance(stats, dict):
        return None
    ratings = stats.get("ratings")
    if not isinstance(ratings, dict) or not ratings:
        return None

    points: list[tuple[int, float]] = []
    for minute_raw, rating_raw in ratings.items():
        # Ratings are often provided as minute-by-minute progression.
        minute = _parse_int(minute_raw)
        rating = _parse_float(rating_raw)
        if minute is None or rating is None:
            continue
        points.append((minute, rating))
    if not points:
        return None
    points.sort(key=lambda item: item[0])
    return points[-1][1]


def empty_rq4_home_away_summary() -> pd.DataFrame:
    """Empty placeholder DataFrame with stable RQ4 columns."""
    return pd.DataFrame(
        columns=[
            "season",
            "season_label",
            "home_away",
            "player",
            "player_id",
            "matches",
            "teams",
            "avg_overall_rating",
            "median_overall_rating",
            "best_overall_rating",
            "worst_overall_rating",
            "starts",
            "motm_awards",
            "eligible_for_leaderboard",
        ]
    )


def _parse_int(value: object) -> int | None:
    """Helper parser: convert robust inputs to `int` or `None`."""
    try:
        if value is None or pd.isna(value):
            return None
    except TypeError:
        if value is None:
            return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _fix_mojibake(text: str) -> str:
    """Fix common mojibake encoding artifacts (e.g. 'Ã¶')."""
    if "Ã" not in text and "Â" not in text:
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def iter_espn_match_summaries(
    config: Config, warn_missing: bool = False
) -> Iterator[tuple[str, Path, dict]]:
    """Iterate over cached ESPN match summaries by season.

    Used in multiple RQ9 steps and encapsulates file + JSON loading.
    """
    for season in config.seasons:
        season_str = str(season)
        summary_dir = config.player_cache_dir / "_espn_match_summaries" / season_str
        if not summary_dir.exists():
            if warn_missing:
                print(
                    f"[warn] RQ9: no match-summary cache found for season {season_str} "
                    f"({summary_dir})."
                )
            continue
        # Each JSON file represents one match summary.
        for match_file in sorted(summary_dir.glob("*.json")):
            with match_file.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            yield season_str, match_file, payload


def load_rq9_team_match_stats(config: Config) -> pd.DataFrame:
    """RQ9: Extract match-level team stats (goals/shots) from ESPN summaries."""
    rows: list[dict] = []
    for season, match_file, payload in iter_espn_match_summaries(config, warn_missing=True):
        # First read goals per side from header competitors (home/away).
        competitors = payload.get("header", {}).get("competitions", [])
        competitors = competitors[0].get("competitors", []) if competitors else []
        goals_by_side: dict[str, int] = {}
        for comp in competitors:
            side = str(comp.get("homeAway") or "").strip().lower()
            if not side:
                continue
            goals = _parse_int(comp.get("score"))
            if goals is None:
                continue
            goals_by_side[side] = goals

        # Then walk team boxscore entries and extract shots + team names.
        for team_data in payload.get("boxscore", {}).get("teams", []):
            side = str(team_data.get("homeAway") or "").strip().lower()
            team_name = (
                team_data.get("team", {}).get("displayName")
                or team_data.get("team", {}).get("name")
                or ""
            ).strip()
            if not side or not team_name:
                continue
            team_name = _fix_mojibake(team_name)
            stats = team_data.get("statistics", [])
            shots_raw = next(
                (s.get("displayValue") for s in stats if s.get("name") == "totalShots"),
                None,
            )
            shots = _parse_int(shots_raw)
            goals = goals_by_side.get(side)
            if shots is None or goals is None:
                continue
            # Keep only records that have both shots and goals.
            rows.append(
                {
                    "season": str(season),
                    "season_label": normalize_season_label(str(season)),
                    "game_id": match_file.stem,
                    "team": team_name,
                    "home_away": side,
                    "goals": goals,
                    "shots": shots,
                }
            )

    columns = [
        "season",
        "season_label",
        "game_id",
        "team",
        "home_away",
        "goals",
        "shots",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame.from_records(rows)[columns]


def compute_rq9_age_vs_efficiency(
    match_stats: pd.DataFrame, team_summary: pd.DataFrame
) -> pd.DataFrame:
    """RQ9: Aggregate efficiency per team and join average team age."""
    columns = [
        "season",
        "season_label",
        "team",
        "avg_age",
        "matches",
        "home_matches",
        "away_matches",
        "total_goals",
        "total_shots",
        "goals_per_shot",
    ]
    if match_stats.empty:
        return pd.DataFrame(columns=columns)

    aggregated = (
        match_stats.groupby(["season", "season_label", "team"], dropna=False)
        .agg(
            matches=("game_id", "nunique"),
            home_matches=("home_away", lambda s: int((s == "home").sum())),
            away_matches=("home_away", lambda s: int((s == "away").sum())),
            total_goals=("goals", "sum"),
            total_shots=("shots", "sum"),
        )
        .reset_index()
    )
    # Core RQ9 metric: goals per shot as efficiency.
    aggregated["goals_per_shot"] = (
        aggregated["total_goals"] / aggregated["total_shots"].replace({0: pd.NA})
    )
    aggregated["season"] = aggregated["season"].astype(str)
    team_age = team_summary[["season", "team", "avg_age"]].copy()
    team_age["season"] = team_age["season"].astype(str)
    rq9 = aggregated.merge(
        team_age,
        how="left",
        on=["season", "team"],
    )
    rq9 = rq9[columns]
    rq9 = rq9.sort_values(
        ["season", "goals_per_shot", "team"],
        ascending=[True, False, True],
        kind="stable",
    )
    return rq9


def compute_rq9_team_match_efficiency(
    match_stats: pd.DataFrame, team_summary: pd.DataFrame
) -> pd.DataFrame:
    """RQ9: Match-level view for spread/distribution plots."""
    columns = [
        "season",
        "season_label",
        "game_id",
        "team",
        "home_away",
        "avg_age",
        "goals",
        "shots",
        "goals_per_shot",
    ]
    if match_stats.empty:
        return pd.DataFrame(columns=columns)

    out = match_stats.copy()
    out["season"] = out["season"].astype(str)
    team_age = team_summary[["season", "team", "avg_age"]].copy()
    team_age["season"] = team_age["season"].astype(str)
    # Match-level output for later spread/variance plots.
    out = out.merge(team_age, how="left", on=["season", "team"])
    out["goals_per_shot"] = out["goals"] / out["shots"].replace({0: pd.NA})
    out = out[columns]
    out = out.sort_values(["season", "game_id", "team"], kind="stable")
    return out


def _fit_rq9_peak(df: pd.DataFrame, scope: str, season: str | None = None) -> dict:
    """Estimate a potential efficiency peak age via quadratic regression."""
    base = {
        "scope": scope,
        "season": season or "all",
        "n_teams": int(len(df)),
        "pearson_r_age_efficiency": float("nan"),
        "estimated_peak_age": float("nan"),
        "estimated_peak_goals_per_shot": float("nan"),
        "model_note": "",
    }
    if df.empty or len(df) < 3:
        base["model_note"] = "Too few data points for peak estimation."
        return base

    x = pd.to_numeric(df["avg_age"], errors="coerce")
    y = pd.to_numeric(df["goals_per_shot"], errors="coerce")
    valid = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(valid) < 3:
        base["model_note"] = "Too few valid data points after cleaning."
        return base

    base["pearson_r_age_efficiency"] = float(valid["x"].corr(valid["y"]))

    # Simple quadratic model: y = a*x^2 + b*x + c.
    coeff = np.polyfit(valid["x"], valid["y"], 2)
    a, b, c = float(coeff[0]), float(coeff[1]), float(coeff[2])
    age_min = float(valid["x"].min())
    age_max = float(valid["x"].max())

    if math.isclose(a, 0.0, abs_tol=1e-12):
        base["model_note"] = "Quadratic model is almost linear; no stable peak age."
        return base
    if a >= 0:
        base["model_note"] = "Curve is not concave; no internal maximum in observed range."
        return base

    # Parabola maximum at x = -b/(2a).
    peak_age = -b / (2 * a)
    if not (age_min <= peak_age <= age_max):
        base["model_note"] = (
            "Maximum lies outside observed age range "
            f"({age_min:.2f}-{age_max:.2f})."
        )
        return base

    peak_eff = a * (peak_age**2) + b * peak_age + c
    base["estimated_peak_age"] = float(peak_age)
    base["estimated_peak_goals_per_shot"] = float(peak_eff)
    base["model_note"] = "Quadratic estimate inside observed age range."
    return base


def compute_rq9_optimal_age_summary(rq9_summary: pd.DataFrame) -> pd.DataFrame:
    """Compute peak estimation once globally and once per season."""
    valid = rq9_summary.dropna(subset=["avg_age", "goals_per_shot"]).copy()
    rows: list[dict] = []
    rows.append(_fit_rq9_peak(valid, scope="all_seasons", season=None))
    for season, group in valid.groupby("season", dropna=False):
        rows.append(_fit_rq9_peak(group, scope="single_season", season=str(season)))
    out = pd.DataFrame.from_records(rows)
    out = out.sort_values(["scope", "season"], kind="stable").reset_index(drop=True)
    return out


def compute_rq9_player_age_profile(config: Config, players_df: pd.DataFrame) -> pd.DataFrame:
    """RQ9: Build goals/shots per age group from player match data."""
    stats_rows: list[dict] = []
    for season, _, payload in iter_espn_match_summaries(config):
        # For each match, read team rosters and extract player stats.
        for team_data in payload.get("rosters", []):
            team_name = (
                team_data.get("team", {}).get("displayName")
                or team_data.get("team", {}).get("name")
                or ""
            ).strip()
            team_name = _fix_mojibake(team_name)
            for player_data in team_data.get("roster", []):
                athlete = player_data.get("athlete", {})
                player_id = str(athlete.get("id") or "").strip()
                player_name = (
                    athlete.get("displayName") or athlete.get("fullName") or ""
                ).strip()
                if not player_id or not player_name:
                    continue
                pstats = player_data.get("stats", []) or []
                goals = next(
                    (_parse_int(s.get("displayValue")) for s in pstats if s.get("name") == "totalGoals"),
                    None,
                )
                shots = next(
                    (_parse_int(s.get("displayValue")) for s in pstats if s.get("name") == "totalShots"),
                    None,
                )
                if goals is None or shots is None:
                    continue
                stats_rows.append(
                    {
                        "season": str(season),
                        "team": team_name,
                        "player": _fix_mojibake(player_name),
                        "player_id": player_id,
                        "goals": goals,
                        "shots": shots,
                    }
                )
    if not stats_rows:
        return pd.DataFrame(
            columns=[
                "season",
                "age_int",
                "players",
                "total_goals",
                "total_shots",
                "goals_per_shot",
            ]
        )

    player_match = pd.DataFrame.from_records(stats_rows)
    # Aggregate on season-team-player level.
    player_totals = (
        player_match.groupby(["season", "team", "player", "player_id"], dropna=False)
        .agg(total_goals=("goals", "sum"), total_shots=("shots", "sum"))
        .reset_index()
    )
    player_totals["player_id"] = player_totals["player_id"].astype(str)

    age_lookup = players_df[["season", "team", "player", "player_id", "age_ref"]].copy()
    age_lookup["season"] = age_lookup["season"].astype(str)
    age_lookup["player_id"] = age_lookup["player_id"].astype(str)
    age_lookup = age_lookup.drop_duplicates(
        subset=["season", "team", "player", "player_id"], keep="first"
    )

    merged = player_totals.merge(
        age_lookup,
        how="left",
        on=["season", "team", "player", "player_id"],
    )
    # Round age to full years so age buckets can be formed.
    merged["age_int"] = pd.to_numeric(merged["age_ref"], errors="coerce").round().astype("Int64")
    merged = merged.dropna(subset=["age_int"])
    merged = merged[merged["total_shots"] > 0].copy()

    by_age = (
        merged.groupby(["season", "age_int"], dropna=False)
        .agg(
            players=("player_id", "nunique"),
            total_goals=("total_goals", "sum"),
            total_shots=("total_shots", "sum"),
        )
        .reset_index()
    )
    by_age["goals_per_shot"] = by_age["total_goals"] / by_age["total_shots"]
    by_age = by_age.sort_values(
        ["season", "goals_per_shot", "age_int"], ascending=[True, False, True], kind="stable"
    )
    return by_age


def compute_rq9_player_best_age(player_age_profile: pd.DataFrame, min_total_shots: int = 80) -> pd.DataFrame:
    """Select best age group by efficiency with minimum sample size."""
    if player_age_profile.empty:
        return pd.DataFrame(
            columns=[
                "season",
                "min_total_shots",
                "best_age_int",
                "goals_per_shot",
                "total_shots",
                "total_goals",
                "players",
            ]
        )
    eligible = player_age_profile[
        pd.to_numeric(player_age_profile["total_shots"], errors="coerce") >= int(min_total_shots)
    ].copy()
    if eligible.empty:
        return pd.DataFrame(
            [
                {
                    "season": "all",
                    "min_total_shots": int(min_total_shots),
                    "best_age_int": pd.NA,
                    "goals_per_shot": pd.NA,
                    "total_shots": pd.NA,
                    "total_goals": pd.NA,
                    "players": pd.NA,
                }
            ]
        )

    out_rows: list[dict] = []
    for season, group in eligible.groupby("season", dropna=False):
        # Ranking priority: high efficiency, then larger sample size.
        best = group.sort_values(
            ["goals_per_shot", "total_shots", "players"],
            ascending=[False, False, False],
            kind="stable",
        ).iloc[0]
        out_rows.append(
            {
                "season": season,
                "min_total_shots": int(min_total_shots),
                "best_age_int": int(best["age_int"]),
                "goals_per_shot": float(best["goals_per_shot"]),
                "total_shots": int(best["total_shots"]),
                "total_goals": int(best["total_goals"]),
                "players": int(best["players"]),
            }
        )

    all_group = (
        eligible.groupby("age_int", dropna=False)
        .agg(
            players=("players", "sum"),
            total_goals=("total_goals", "sum"),
            total_shots=("total_shots", "sum"),
        )
        .reset_index()
    )
    all_group["goals_per_shot"] = all_group["total_goals"] / all_group["total_shots"]
    best_all = all_group.sort_values(
        ["goals_per_shot", "total_shots", "players"],
        ascending=[False, False, False],
        kind="stable",
    ).iloc[0]
    out_rows.append(
        {
            "season": "all",
            "min_total_shots": int(min_total_shots),
            "best_age_int": int(best_all["age_int"]),
            "goals_per_shot": float(best_all["goals_per_shot"]),
            "total_shots": int(best_all["total_shots"]),
            "total_goals": int(best_all["total_goals"]),
            "players": int(best_all["players"]),
        }
    )

    return pd.DataFrame.from_records(out_rows).sort_values(["season"], kind="stable")


def compute_rq9_outputs(config: Config, core: CoreOutputs, players_df: pd.DataFrame) -> RQ9Outputs:
    """Compute all RQ9 tables from match and age data."""
    # Order: raw match stats -> team summary -> peak estimate -> player age profile.
    match_stats = load_rq9_team_match_stats(config)
    summary = compute_rq9_age_vs_efficiency(match_stats, core.team_summary)
    match_efficiency = compute_rq9_team_match_efficiency(match_stats, core.team_summary)
    peak_summary = compute_rq9_optimal_age_summary(summary)
    player_age_profile = compute_rq9_player_age_profile(config, players_df)
    player_best_age = compute_rq9_player_best_age(player_age_profile, min_total_shots=80)
    return RQ9Outputs(
        summary=summary,
        match_efficiency=match_efficiency,
        peak_summary=peak_summary,
        player_age_profile=player_age_profile,
        player_best_age=player_best_age,
    )


def save_outputs(
    core: CoreOutputs,
    rq4: RQ4Outputs,
    rq9: RQ9Outputs,
    output_dir: Path,
) -> dict[str, list[Path]]:
    """Write all result DataFrames to disk as grouped CSV files."""
    export_groups: dict[str, list[tuple[str, pd.DataFrame]]] = {
        "core": [
            ("bundesliga_team_player_ages.csv", core.player_table),
            ("bundesliga_team_age_summary.csv", core.team_summary),
            ("bundesliga_season_age_summary.csv", core.season_summary),
            ("bundesliga_global_age_summary.csv", core.global_summary),
        ],
        "rq4": [
            ("rq4_home_away_player_ratings.csv", rq4.summary),
            ("rq4_player_home_away_delta.csv", rq4.delta),
        ],
        "rq9": [
            ("rq9_team_age_vs_efficiency.csv", rq9.summary),
            ("rq9_team_match_efficiency.csv", rq9.match_efficiency),
            ("rq9_optimal_age_summary.csv", rq9.peak_summary),
            ("rq9_player_age_profile.csv", rq9.player_age_profile),
            ("rq9_player_best_age.csv", rq9.player_best_age),
        ],
    }
    written_files: dict[str, list[Path]] = {}
    for group_name, group_exports in export_groups.items():
        # Each group (core/rq4/rq9) gets its own subdirectory.
        group_dir = output_dir / group_name
        group_dir.mkdir(parents=True, exist_ok=True)
        written_files[group_name] = []
        for filename, df in group_exports:
            path = group_dir / filename
            df.to_csv(path, index=False)
            written_files[group_name].append(path)
    return written_files


def round_numeric_columns(
    df: pd.DataFrame, columns: Iterable[str], digits: int
) -> pd.DataFrame:
    """Round selected numeric columns for readable reports."""
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(digits)
    return out


def print_output_manifest(output_files: dict[str, list[Path]]) -> None:
    """Print a compact list of written CSV files at the end."""
    print("\n=== CSV OUTPUTS (BY AREA) ===")
    for group in ("core", "rq4", "rq9"):
        files = output_files.get(group, [])
        print(f"\n[{group.upper()}]")
        if not files:
            print("  (no files)")
            continue
        for path in files:
            print(f"  - {path.name}")


def print_report(core: CoreOutputs, rq4: RQ4Outputs, rq9: RQ9Outputs) -> None:
    """Print compact console report for core, RQ4, and RQ9."""
    # Higher display limits so tables are not cut off too early.
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.width", 200)

    print("\n=== TEAM AVERAGE AGE BY SEASON ===")
    team_display = round_numeric_columns(core.team_summary, ("avg_age", "min_age", "max_age"), 2)
    print(team_display.to_string(index=False))

    print("\n=== SEASON SUMMARY (LEAGUE-WIDE, DEDUP PER PLAYER/SEASON) ===")
    season_display = round_numeric_columns(
        core.season_summary, ("avg_age", "min_age", "max_age"), 2
    )
    print(season_display.to_string(index=False))

    print("\n=== GLOBAL AVERAGE AGE ACROSS ALL TEAMS/SEASONS ===")
    global_display = round_numeric_columns(
        core.global_summary, ("avg_age", "min_age", "max_age"), 2
    )
    print(global_display.to_string(index=False))

    print("\n=== RQ4: HOME/AWAY PERFORMANCE BY WHOSCORED OVERALL RATING ===")
    if rq4.summary.empty:
        print("[warn] No RQ4 data available.")
    else:
        rq4_display = round_numeric_columns(
            rq4.summary,
            (
                "avg_overall_rating",
                "median_overall_rating",
                "best_overall_rating",
                "worst_overall_rating",
            ),
            3,
        )

        eligible = rq4_display[
            pd.to_numeric(rq4_display["matches"], errors="coerce")
            >= RQ4_MIN_MATCHES_FOR_LEADERBOARD
        ].copy()
        # If nobody meets minimum matches, still show available rows.
        if eligible.empty:
            eligible = rq4_display.copy()
        for (season_label, side), group in eligible.groupby(
            ["season_label", "home_away"], sort=True
        ):
            print(
                f"\n[{season_label}] {str(side).upper()} "
                f"(min. {RQ4_MIN_MATCHES_FOR_LEADERBOARD} matches)"
            )
            cols = [
                "player",
                "matches",
                "avg_overall_rating",
                "median_overall_rating",
                "best_overall_rating",
                "worst_overall_rating",
                "starts",
                "motm_awards",
            ]
            top_group = group.sort_values(
                ["avg_overall_rating", "matches", "player"],
                ascending=[False, False, True],
                kind="stable",
            ).head(10)
            print(top_group[cols].to_string(index=False))

    print("\n=== RQ4: HOME VS AWAY DELTA (AVG RATING) ===")
    if rq4.delta.empty:
        print("[warn] No RQ4 delta data available.")
    else:
        delta_display = round_numeric_columns(
            rq4.delta,
            (
                "home_avg_overall_rating",
                "away_avg_overall_rating",
                "avg_rating_delta_home_minus_away",
                "abs_avg_rating_delta",
            ),
            3,
        )
        delta_cols = [
            "season_label",
            "player",
            "home_matches",
            "away_matches",
            "avg_rating_delta_home_minus_away",
            "abs_avg_rating_delta",
            "eligible_both_sides",
        ]
        print(delta_display[delta_cols].head(15).to_string(index=False))

    print("\n=== RQ9: TEAM AGE VS EFFICIENCY (GOALS PER SHOT) ===")
    rq9_display = round_numeric_columns(rq9.summary, ("avg_age", "goals_per_shot"), 3)
    print(rq9_display.to_string(index=False))

    print("\n=== RQ9: MATCH-LEVEL TEAM AGE VS EFFICIENCY (EXCERPT) ===")
    if rq9.match_efficiency.empty:
        print("[warn] No RQ9 match-level data available.")
    else:
        match_display = round_numeric_columns(
            rq9.match_efficiency, ("avg_age", "goals_per_shot"), 3
        )
        match_cols = [
            "season_label",
            "game_id",
            "team",
            "home_away",
            "avg_age",
            "goals",
            "shots",
            "goals_per_shot",
        ]
        print(match_display[match_cols].head(20).to_string(index=False))

    print("\n=== RQ9: ESTIMATED 'BEST' AGE ===")
    peak_display = round_numeric_columns(
        rq9.peak_summary,
        (
            "pearson_r_age_efficiency",
            "estimated_peak_age",
            "estimated_peak_goals_per_shot",
        ),
        3,
    )
    print(peak_display.to_string(index=False))

    print("\n=== RQ9: PLAYER AGE PROFILE (GOALS PER SHOT) ===")
    profile_display = round_numeric_columns(rq9.player_age_profile, ("goals_per_shot",), 3)
    print(profile_display.to_string(index=False))

    print("\n=== RQ9: 'BEST' PLAYER AGE (BY AGE GROUP) ===")
    best_display = round_numeric_columns(rq9.player_best_age, ("goals_per_shot",), 3)
    print(best_display.to_string(index=False))


def build_config(args: argparse.Namespace) -> Config:
    """Validate CLI arguments and build internal Config object."""
    seasons = [str(s).strip() for s in args.seasons if str(s).strip()]
    if not seasons:
        raise SystemExit("At least one season must be provided.")
    invalid_seasons = [s for s in seasons if s != TARGET_SEASON]
    if invalid_seasons or len(seasons) != 1:
        raise SystemExit(
            "This script is fixed to Bundesliga season 2024/25 (2425). "
            "Please use --seasons 2425."
        )
    # Hard restriction ensures consistent comparability across outputs.
    seasons = [TARGET_SEASON]
    source_priority = [
        str(s).strip().lower() for s in args.source_priority if str(s).strip()
    ]
    if not source_priority:
        raise SystemExit("Provide at least one data source in --source-priority.")
    allowed_sources = {"espn"}
    invalid_sources = [s for s in source_priority if s not in allowed_sources]
    if invalid_sources:
        raise SystemExit(
            "Invalid data source in --source-priority: "
            f"{', '.join(invalid_sources)}. Only allowed: espn."
        )
    # Pipeline is intentionally fixed to ESPN for now.
    source_priority = ["espn"]
    return Config(
        seasons=seasons,
        league=str(args.league).strip(),
        soccerdata_cache_dir=Path(args.soccerdata_cache_dir),
        player_cache_dir=Path(args.player_cache_dir),
        output_dir=Path(args.output_dir),
        refresh=bool(args.refresh),
        no_cache=bool(args.no_cache),
        no_store=bool(args.no_store),
        proxy=args.proxy,
        source_priority=source_priority,
    )


def main(argv: Iterable[str] | None = None) -> int:
    # 1) Prepare configuration and environment variables.
    args = parse_args(argv)
    config = build_config(args)
    configure_env(config)

    try:
        # 2) Load shared input data (players per season).
        players_df = load_players_for_config(config)
    except Exception as exc:
        print(f"[error] Data retrieval failed: {exc}")
        print(
            "[hint] This script only uses ESPN. "
            "If fetching fails, check network/proxy (option --proxy)."
        )
        return 1

    # 3) Compute results in three clear areas: core, RQ4, RQ9.
    core = compute_core_outputs(players_df)
    rq4 = compute_rq4_outputs(config)
    rq9 = compute_rq9_outputs(config, core, players_df)

    # 4) Persist results and print console summary.
    output_files = save_outputs(
        core=core,
        rq4=rq4,
        rq9=rq9,
        output_dir=config.output_dir,
    )
    print_report(core, rq4, rq9)
    print_output_manifest(output_files)

    print("\n[ok] CSV outputs saved to:", config.output_dir.resolve())
    print("[ok] Season player caches in:", config.player_cache_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
