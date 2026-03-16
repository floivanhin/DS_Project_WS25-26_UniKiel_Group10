"""Build the WhoScored dataset used for RQ4.

Input: pipeline configuration with league, season, and refresh mode.
Output: one CSV-ready DataFrame with player match ratings.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from pipeline_config import Config
from pipeline_utils import (
    ensure_soccerdata,
    fix_mojibake,
    format_progress,
    normalize_season_label,
    should_log_progress,
)


WHOSCORED_MATCH_COLUMNS = [
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


def build_whoscored_dataset(config: Config) -> pd.DataFrame:
    """Load and return the full WhoScored player match dataset.

    Input: Config instance.
    Output: DataFrame with one row per match and player.
    """
    return load_whoscored_match_rows(config)


def load_whoscored_match_rows(config: Config) -> pd.DataFrame:
    """Read schedule and event files and turn them into match rows.

    Input: Config instance.
    Output: sorted DataFrame with WhoScored match rows.
    """
    sd = ensure_soccerdata()
    whoscored = sd.WhoScored(leagues=config.league, seasons=[config.season])
    print(f"[info] WhoScored: loading schedule for season {config.season} ...")
    schedule = whoscored.read_schedule(
        force_cache=not config.refresh,
    ).reset_index()
    if schedule.empty:
        return pd.DataFrame(columns=WHOSCORED_MATCH_COLUMNS)

    required_schedule = {"game_id", "home_team", "away_team"}
    missing = [col for col in required_schedule if col not in schedule.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            "WhoScored schedule is missing expected columns: "
            f"{missing_text}"
        )

    schedule["game_id"] = schedule["game_id"].apply(to_int_or_none)
    schedule = schedule.dropna(subset=["game_id"]).copy()
    schedule["game_id"] = schedule["game_id"].astype(int)
    schedule["season"] = schedule["season"].astype(str)

    league_key = (
        str(schedule.iloc[0]["league"]).strip()
        if "league" in schedule.columns
        else config.league
    )
    events_dir = (
        Path(whoscored.data_dir)
        / "events"
        / f"{league_key}_{config.season}"
    )
    game_ids = sorted(schedule["game_id"].dropna().astype(int).unique())
    existing_ids = {
        game_id
        for game_id in game_ids
        if (events_dir / f"{game_id}.json").exists()
    }
    ids_to_fetch = (
        game_ids
        if config.refresh
        else [
            game_id
            for game_id in game_ids
            if game_id not in existing_ids
        ]
    )

    print(
        f"[info] WhoScored: matches={len(game_ids)}, "
        f"cache={len(existing_ids)}, download={len(ids_to_fetch)}"
    )
    if ids_to_fetch:
        print(
            f"{format_progress('WhoScored download', 0, len(ids_to_fetch))} | "
            f"remaining={len(ids_to_fetch)}",
            flush=True,
        )
        whoscored.read_events(
            match_id=ids_to_fetch,
            force_cache=not config.refresh,
            output_fmt=None,
            on_error="skip",
        )
        print(
            f"{format_progress(
                'WhoScored download',
                len(ids_to_fetch),
                len(ids_to_fetch),
            )} | remaining=0",
            flush=True,
        )

    metadata = schedule.drop_duplicates(
        subset=["game_id"],
        keep="first",
    ).set_index("game_id")
    rows: list[dict] = []
    total = len(game_ids)
    interval = max(1, total // 20) if total else 1
    for idx, game_id in enumerate(game_ids, start=1):
        event_file = events_dir / f"{game_id}.json"
        if not event_file.exists():
            continue
        with event_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows.extend(
            parse_event_payload(
                payload,
                metadata.loc[game_id],
                config.season,
                game_id,
            )
        )
        if should_log_progress(idx, total, interval):
            print(format_progress("WhoScored matches", idx, total), flush=True)

    return (
        pd.DataFrame.from_records(rows, columns=WHOSCORED_MATCH_COLUMNS)
        .sort_values(
            ["season", "game_id", "home_away", "player"],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def parse_event_payload(
    payload: dict,
    metadata: pd.Series,
    season: str,
    game_id: int,
) -> list[dict]:
    """Convert one WhoScored event payload into row dictionaries.

    Input: raw payload, schedule metadata, season, and game id.
    Output: list of row dictionaries.
    """
    home_team = fix_mojibake(str(metadata.get("home_team") or "").strip())
    away_team = fix_mojibake(str(metadata.get("away_team") or "").strip())
    game_label = str(metadata.get("game") or "").strip()
    rows: list[dict] = []

    for side in ("home", "away"):
        side_data = payload.get(side, {})
        if not isinstance(side_data, dict):
            continue

        team_name = fix_mojibake(str(side_data.get("name") or "").strip())
        if not team_name:
            team_name = home_team if side == "home" else away_team

        players = side_data.get("players", [])
        if not isinstance(players, list):
            continue

        for player_data in players:
            if not isinstance(player_data, dict):
                continue

            player_id = str(player_data.get("playerId") or "").strip()
            player_name = fix_mojibake(
                str(player_data.get("name") or "").strip()
            )
            overall_rating = extract_overall_rating(player_data)
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
                    "overall_rating": overall_rating,
                    "is_starting_xi": bool(player_data.get("isFirstEleven")),
                    "is_man_of_the_match": bool(
                        player_data.get("isManOfTheMatch")
                    ),
                }
            )
    return rows


def extract_overall_rating(player_data: dict) -> float | None:
    """Read the latest available player rating from a payload item.

    Input: one player dictionary from a WhoScored event file.
    Output: float rating or `None`.
    """
    ratings = player_data.get("ratings")
    if not isinstance(ratings, dict):
        ratings = player_data.get("stats", {}).get("ratings")

    if isinstance(ratings, dict) and ratings:
        numeric: list[float] = []
        ordered_keys = sorted(
            ratings.keys(),
            key=lambda value: to_int_or_none(value) or 0,
        )
        for key in ordered_keys:
            value = to_float_or_none(ratings.get(key))
            if value is not None:
                numeric.append(value)
        if numeric:
            return float(numeric[-1])

    return to_float_or_none(player_data.get("rating"))
