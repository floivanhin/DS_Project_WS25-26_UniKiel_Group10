import json
import math
from pathlib import Path

import pandas as pd


# columns for the raw whoscored csv
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


# make 2425 -> 2024/2025
def season_label(season):
    season = str(season).strip()
    if len(season) == 4 and season.isdigit():
        return f"20{season[:2]}/20{season[2:]}"
    return season


# fix weird text
def clean_text(text):
    if not text:
        return text
    if not any(ch in text for ch in ("\u00c3", "\u00e2", "\u20ac", "\u2122")):
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


# try to get an int
def to_int(value):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


# try to get a float
def to_float(value):
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


# get the last rating we can find
def latest_rating(player_data):
    ratings = player_data.get("ratings")
    if not isinstance(ratings, dict):
        ratings = player_data.get("stats", {}).get("ratings")

    if isinstance(ratings, dict) and ratings:
        numeric = []
        for key in sorted(ratings.keys(), key=lambda value: to_int(value) or 0):
            value = to_float(ratings.get(key))
            if value is not None:
                numeric.append(value)
        if numeric:
            return float(numeric[-1])

    return to_float(player_data.get("rating"))


# turn one match json into rows
def parse_match(payload, metadata, season, game_id):
    home_team = clean_text(str(metadata.get("home_team") or "").strip())
    away_team = clean_text(str(metadata.get("away_team") or "").strip())
    game_label = str(metadata.get("game") or "").strip()

    rows = []
    for side in ["home", "away"]:
        # home and away are stored separately
        side_data = payload.get(side, {})
        if not isinstance(side_data, dict):
            continue

        team_name = clean_text(str(side_data.get("name") or "").strip())
        if not team_name:
            team_name = home_team if side == "home" else away_team

        players = side_data.get("players", [])
        if not isinstance(players, list):
            continue

        # make one row per player
        for player_data in players:
            if not isinstance(player_data, dict):
                continue

            player_id = str(player_data.get("playerId") or "").strip()
            player_name = clean_text(str(player_data.get("name") or "").strip())
            overall_rating = latest_rating(player_data)
            if not player_id or not player_name or overall_rating is None:
                continue

            rows.append(
                {
                    "season": str(season),
                    "season_label": season_label(season),
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


# load all whoscored rows
def build_whoscored_dataset(league, season, refresh=False):
    import soccerdata as sd

    whoscored = sd.WhoScored(leagues=league, seasons=[season])
    print(f"WhoScored schedule {season}")
    schedule = whoscored.read_schedule(force_cache=not refresh).reset_index()
    if schedule.empty:
        return pd.DataFrame(columns=WHOSCORED_MATCH_COLUMNS)

    schedule["game_id"] = schedule["game_id"].apply(to_int)
    schedule = schedule.dropna(subset=["game_id"]).copy()
    if schedule.empty:
        return pd.DataFrame(columns=WHOSCORED_MATCH_COLUMNS)

    schedule["game_id"] = schedule["game_id"].astype(int)

    league_key = (
        str(schedule.iloc[0]["league"]).strip()
        if "league" in schedule.columns
        else league
    )
    events_dir = Path(whoscored.data_dir) / "events" / f"{league_key}_{season}"
    game_ids = sorted(schedule["game_id"].unique().tolist())

    # only fetch missing files unless refresh is on
    if refresh:
        ids_to_fetch = game_ids
    else:
        ids_to_fetch = [
            game_id
            for game_id in game_ids
            if not (events_dir / f"{game_id}.json").exists()
        ]

    if ids_to_fetch:
        print(f"WhoScored downloads {len(ids_to_fetch)}")
        whoscored.read_events(
            match_id=ids_to_fetch,
            force_cache=not refresh,
            output_fmt=None,
            on_error="skip",
        )

    # quick lookup for game labels
    rows = []
    total = len(game_ids)
    metadata = schedule.drop_duplicates(subset=["game_id"], keep="first").set_index(
        "game_id"
    )

    # read cached event files
    for i, game_id in enumerate(game_ids, start=1):
        event_file = events_dir / f"{game_id}.json"
        if event_file.exists():
            with event_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            rows.extend(parse_match(payload, metadata.loc[game_id], season, game_id))

        if i == 1 or i % 25 == 0 or i == total:
            print(f"WhoScored matches {i}/{total}")

    # final order for the csv
    return pd.DataFrame(rows, columns=WHOSCORED_MATCH_COLUMNS).sort_values(
        ["season", "game_id", "home_away", "player"],
        kind="stable",
    ).reset_index(drop=True)
