"""Build the ESPN dataset used for RQ8.

Input: pipeline configuration with league, season, and refresh mode.
Output: one CSV-ready DataFrame with player and team shooting data.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import requests

from pipeline_config import Config
from pipeline_utils import (
    ESPN_ATHLETE_URL,
    age_years_at_reference_date,
    ensure_soccerdata,
    fix_mojibake,
    format_progress,
    normalize_season_label,
    parse_espn_display_dob,
    season_reference_date,
    should_log_progress,
)


ESPN_ANALYSIS_COLUMNS = [
    "season",
    "season_label",
    "game_id",
    "team",
    "player",
    "player_id",
    "age",
    "player_goals",
    "player_shots",
    "team_goals",
    "team_shots",
]
PLAYER_COLUMNS = [
    "season",
    "season_label",
    "team",
    "player",
    "player_id",
    "appearances",
    "age_ref",
]


def to_int_or_none(value: object) -> int | None:
    """Convert one loose value into an integer when possible.

    Input: raw source value.
    Output: integer value or `None`.
    """
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def to_float_or_none(value: object) -> float | None:
    """Convert one loose value into a float when possible.

    Input: raw source value.
    Output: float value or `None`.
    """
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def build_espn_dataset(config: Config) -> pd.DataFrame:
    """Load and return the full ESPN player shooting dataset.

    Input: Config instance.
    Output: DataFrame with one row per match, team, and player.
    """
    players = load_players(config)
    return build_espn_analysis_rows(config, players)


def load_players(config: Config) -> pd.DataFrame:
    """Load season player rows and merge age data from ESPN profiles.

    Input: Config instance.
    Output: DataFrame with player season rows and age references.
    """
    sd = ensure_soccerdata()
    espn = sd.ESPN(leagues=config.league, seasons=[config.season])
    schedule = espn.read_schedule().reset_index()
    if schedule.empty:
        return pd.DataFrame(columns=PLAYER_COLUMNS)

    roster_rows: list[dict] = []
    total_matches = len(schedule)
    interval = max(1, total_matches // 20)
    print(f"[info] ESPN: loading match sheets for season {config.season} ...")
    for idx, match in enumerate(schedule.itertuples(index=False), start=1):
        matchsheet = espn.read_matchsheet(
            match_id=int(match.game_id),
        ).reset_index()
        for row in matchsheet.itertuples(index=False):
            roster = row.roster if isinstance(row.roster, list) else []
            for player_data in roster:
                athlete = player_data.get("athlete", {})
                player_id = str(athlete.get("id") or "").strip()
                player_name = (
                    athlete.get("displayName")
                    or athlete.get("fullName")
                    or ""
                ).strip()
                if not player_id or not player_name:
                    continue

                roster_rows.append(
                    {
                        "season": str(row.season),
                        "season_label": normalize_season_label(
                            str(row.season)
                        ),
                        "team": fix_mojibake(str(row.team)),
                        "player": fix_mojibake(player_name),
                        "player_id": player_id,
                        "game": str(row.game),
                    }
                )
        if should_log_progress(idx, total_matches, interval):
            print(
                format_progress("ESPN match sheets", idx, total_matches),
                flush=True,
            )

    roster_df = pd.DataFrame.from_records(roster_rows)
    if roster_df.empty:
        return pd.DataFrame(columns=PLAYER_COLUMNS)

    players = (
        roster_df.drop_duplicates(
            subset=["season", "team", "player_id", "game"],
            keep="first",
        )
        .groupby(
            ["season", "season_label", "team", "player", "player_id"],
            dropna=False,
        )
        .agg(appearances=("game", "nunique"))
        .reset_index()
    )
    profiles = fetch_athlete_profiles(
        player_ids=players["player_id"].dropna().astype(str).unique().tolist(),
        reference_date=season_reference_date(config.season),
    )
    players = players.merge(profiles, how="left", on="player_id")
    return players[PLAYER_COLUMNS].copy()


def fetch_athlete_profiles(
    player_ids: list[str],
    reference_date,
) -> pd.DataFrame:
    """Fetch player profile data and derive an age value.

    Input: player id list and reference date.
    Output: DataFrame with `player_id` and `age_ref`.
    """
    session = requests.Session()
    rows: list[dict] = []
    total = len(player_ids)
    interval = max(1, total // 20) if total else 1

    for idx, player_id in enumerate(sorted(player_ids), start=1):
        payload: dict = {}
        try:
            response = session.get(
                ESPN_ATHLETE_URL.format(athlete_id=player_id),
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json().get("athlete", {})
        except (requests.RequestException, ValueError):
            # Missing or malformed profile payloads are allowed here.
            payload = {}

        birth_date = parse_espn_display_dob(payload.get("displayDOB"))
        age_ref = (
            age_years_at_reference_date(birth_date, reference_date)
            if birth_date is not None
            else to_float_or_none(payload.get("age"))
        )
        rows.append({"player_id": player_id, "age_ref": age_ref})
        if should_log_progress(idx, total, interval):
            print(
                format_progress("ESPN athlete profiles", idx, total),
                flush=True,
            )

    return pd.DataFrame.from_records(rows)


def load_team_match_stats(config: Config) -> list[dict]:
    """Load team and player shooting stats from cached ESPN summaries.

    Input: Config instance.
    Output: list of row dictionaries.
    """
    sd = ensure_soccerdata()
    espn = sd.ESPN(leagues=config.league, seasons=[config.season])
    schedule = espn.read_schedule().reset_index()
    if schedule.empty:
        return []

    print("[info] ESPN: loading match sheets for team match stats ...")
    espn.read_matchsheet()
    summary_root = Path(espn.data_dir)
    return parse_summary_files_from_schedule(
        summary_root,
        schedule,
        config.season,
    )


def parse_summary_files_from_schedule(
    summary_root: Path,
    schedule: pd.DataFrame,
    season: str,
) -> list[dict]:
    """Read all cached summary JSON files for one schedule.

    Input: summary root path, schedule DataFrame, and season string.
    Output: list of row dictionaries.
    """
    rows: list[dict] = []
    total = len(schedule)
    interval = max(1, total // 20) if total else 1
    for idx, match in enumerate(schedule.itertuples(index=False), start=1):
        game_id = str(match.game_id)
        summary_file = summary_root / f"Summary_{game_id}.json"
        if not summary_file.exists():
            continue
        with summary_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows.extend(parse_summary_payload(payload, season, game_id))
        if should_log_progress(idx, total, interval):
            print(
                format_progress("ESPN summaries cached", idx, total),
                flush=True,
            )
    return rows


def parse_summary_payload(
    payload: dict,
    season: str,
    game_id: str,
) -> list[dict]:
    """Turn one ESPN summary payload into analysis rows.

    Input: raw summary payload, season, and game id.
    Output: list of row dictionaries.
    """
    competitions = payload.get("header", {}).get("competitions", [])
    competitors = []
    if competitions:
        competitors = competitions[0].get("competitors", [])

    goals_by_side: dict[str, int] = {}
    for competitor in competitors:
        side = str(competitor.get("homeAway") or "").strip().lower()
        goals = to_int_or_none(competitor.get("score"))
        if side and goals is not None:
            goals_by_side[side] = goals

    team_rows: list[dict] = []
    for team_data in payload.get("boxscore", {}).get("teams", []):
        side = str(team_data.get("homeAway") or "").strip().lower()
        team_name = (
            team_data.get("team", {}).get("displayName")
            or team_data.get("team", {}).get("name")
            or ""
        ).strip()
        stats = team_data.get("statistics", [])
        shots = to_int_or_none(
            next(
                (
                    stat.get("displayValue")
                    for stat in stats
                    if stat.get("name") == "totalShots"
                ),
                None,
            )
        )
        goals = goals_by_side.get(side)
        if not side or not team_name or shots is None or goals is None:
            continue

        team_rows.append(
            {
                "season": str(season),
                "season_label": normalize_season_label(str(season)),
                "game_id": str(game_id),
                "team": fix_mojibake(team_name),
                "home_away": side,
                "goals": goals,
                "shots": shots,
            }
        )

    rows: list[dict] = []
    for team_data in payload.get("rosters", []):
        team_name = (
            team_data.get("team", {}).get("displayName")
            or team_data.get("team", {}).get("name")
            or ""
        ).strip()
        team_name = fix_mojibake(team_name)
        matched_team = None
        for candidate in team_rows:
            if candidate["team"] == team_name:
                matched_team = candidate
                break
        if matched_team is None:
            continue

        for player_data in team_data.get("roster", []):
            athlete = player_data.get("athlete", {})
            player_id = str(athlete.get("id") or "").strip()
            player_name = (
                athlete.get("displayName")
                or athlete.get("fullName")
                or ""
            ).strip()
            if not player_id or not player_name:
                continue

            stats = player_data.get("stats", []) or []
            player_goals = to_int_or_none(
                next(
                    (
                        stat.get("displayValue")
                        for stat in stats
                        if stat.get("name") == "totalGoals"
                    ),
                    0,
                )
            )
            player_shots = to_int_or_none(
                next(
                    (
                        stat.get("displayValue")
                        for stat in stats
                        if stat.get("name") == "totalShots"
                    ),
                    0,
                )
            )
            rows.append(
                {
                    "season": str(season),
                    "season_label": normalize_season_label(str(season)),
                    "game_id": str(game_id),
                    "team": matched_team["team"],
                    "player": fix_mojibake(player_name),
                    "player_id": player_id,
                    "player_goals": (
                        0 if player_goals is None else player_goals
                    ),
                    "player_shots": (
                        0 if player_shots is None else player_shots
                    ),
                    "team_goals": matched_team["goals"],
                    "team_shots": matched_team["shots"],
                }
            )
    return rows


def build_espn_analysis_rows(
    config: Config,
    players: pd.DataFrame,
) -> pd.DataFrame:
    """Combine match shooting rows with player age references.

    Input: Config instance and player DataFrame.
    Output: sorted ESPN analysis DataFrame.
    """
    rows = load_team_match_stats(config)
    if not rows:
        return pd.DataFrame(columns=ESPN_ANALYSIS_COLUMNS)

    out = pd.DataFrame.from_records(rows)
    age_lookup = players[
        ["season", "team", "player", "player_id", "age_ref"]
    ].copy()
    age_lookup["season"] = age_lookup["season"].astype(str)
    age_lookup["team"] = age_lookup["team"].astype(str)
    age_lookup["player"] = age_lookup["player"].astype(str)
    age_lookup["player_id"] = age_lookup["player_id"].astype(str)
    age_lookup = age_lookup.drop_duplicates(
        subset=["season", "team", "player", "player_id"],
        keep="first",
    )

    out["season"] = out["season"].astype(str)
    out["team"] = out["team"].astype(str)
    out["player"] = out["player"].astype(str)
    out["player_id"] = out["player_id"].astype(str)
    out = out.merge(
        age_lookup,
        how="left",
        on=["season", "team", "player", "player_id"],
    )
    out = out.rename(columns={"age_ref": "age"})
    return out[ESPN_ANALYSIS_COLUMNS].sort_values(
        ["season", "game_id", "team", "player"],
        kind="stable",
    )
