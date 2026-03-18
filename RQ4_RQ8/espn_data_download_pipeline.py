import json
import math
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests


ESPN_ATHLETE_URL = (
    "https://site.web.api.espn.com/apis/common/v3/sports/"
    "soccer/athletes/{athlete_id}"
)

# columns for the raw espn csv
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


# read espn date text
def parse_dob(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%MZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


# age on one date
def age_at(birth_date, ref_date):
    return (ref_date - birth_date).days / 365.25


# ask espn for player ages
def fetch_player_ages(player_ids, ref_date):
    session = requests.Session()
    rows = []
    total = len(player_ids)

    for i, player_id in enumerate(sorted(player_ids), start=1):
        age = None
        try:
            # grab one profile
            response = session.get(
                ESPN_ATHLETE_URL.format(athlete_id=player_id),
                timeout=30,
            )
            response.raise_for_status()
            athlete = response.json().get("athlete", {})
            birth_date = parse_dob(athlete.get("displayDOB"))
            if birth_date is not None:
                age = age_at(birth_date, ref_date)
            else:
                age = to_float(athlete.get("age"))
        except (requests.RequestException, ValueError):
            pass

        rows.append({"player_id": str(player_id), "age_ref": age})
        if i == 1 or i % 50 == 0 or i == total:
            print(f"ESPN player ages {i}/{total}")

    return pd.DataFrame(rows)


# turn one summary json into rows
def parse_summary(payload, season, game_id):
    competitions = payload.get("header", {}).get("competitions", [])
    competitors = competitions[0].get("competitors", []) if competitions else []

    # get team goals first
    team_rows = []
    goals_by_side = {}
    for competitor in competitors:
        side = str(competitor.get("homeAway") or "").strip().lower()
        goals = to_int(competitor.get("score"))
        if side and goals is not None:
            goals_by_side[side] = goals

    # get team shots
    for team_data in payload.get("boxscore", {}).get("teams", []):
        side = str(team_data.get("homeAway") or "").strip().lower()
        team_name = (
            team_data.get("team", {}).get("displayName")
            or team_data.get("team", {}).get("name")
            or ""
        ).strip()
        shots = None
        for stat in team_data.get("statistics", []):
            if stat.get("name") == "totalShots":
                shots = to_int(stat.get("displayValue"))
                break
        goals = goals_by_side.get(side)
        if not side or not team_name or shots is None or goals is None:
            continue
        team_rows.append(
            {
                "team": clean_text(team_name),
                "side": side,
                "goals": goals,
                "shots": shots,
            }
        )

    # now get player rows
    rows = []
    for team_data in payload.get("rosters", []):
        team_name = (
            team_data.get("team", {}).get("displayName")
            or team_data.get("team", {}).get("name")
            or ""
        ).strip()
        team_name = clean_text(team_name)

        matched_team = None
        for candidate in team_rows:
            if candidate["team"] == team_name:
                matched_team = candidate
                break

        if matched_team is None:
            continue

        # player stats from the roster part
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

            player_goals = 0
            player_shots = 0
            for stat in player_data.get("stats", []) or []:
                if stat.get("name") == "totalGoals":
                    value = to_int(stat.get("displayValue"))
                    if value is not None:
                        player_goals = value
                elif stat.get("name") == "totalShots":
                    value = to_int(stat.get("displayValue"))
                    if value is not None:
                        player_shots = value

            rows.append(
                {
                    "season": str(season),
                    "season_label": season_label(season),
                    "game_id": str(game_id),
                    "team": matched_team["team"],
                    "player": clean_text(player_name),
                    "player_id": player_id,
                    "player_goals": player_goals,
                    "player_shots": player_shots,
                    "team_goals": matched_team["goals"],
                    "team_shots": matched_team["shots"],
                }
            )

    return rows


# load all espn data we need
def build_espn_dataset(league, season, refresh=False):
    import soccerdata as sd

    espn = sd.ESPN(leagues=league, seasons=[season])
    print(f"ESPN schedule {season}")
    schedule = espn.read_schedule(force_cache=not refresh).reset_index()
    if schedule.empty:
        return pd.DataFrame(columns=ESPN_ANALYSIS_COLUMNS)

    roster_rows = []
    total_matches = len(schedule)

    print("ESPN match sheets")
    for i, match in enumerate(schedule.itertuples(index=False), start=1):
        game_id = to_int(getattr(match, "game_id", None))
        if game_id is None:
            continue

        # pull players from one match
        matchsheet = espn.read_matchsheet(match_id=game_id).reset_index()
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
                        "team": clean_text(str(row.team)),
                        "player": clean_text(player_name),
                        "player_id": player_id,
                    }
                )

        if i == 1 or i % 25 == 0 or i == total_matches:
            print(f"ESPN match sheets {i}/{total_matches}")

    # one row per player for age lookup
    players = pd.DataFrame(roster_rows)
    if players.empty:
        age_lookup = pd.DataFrame(columns=["season", "team", "player", "player_id", "age_ref"])
    else:
        players = players.drop_duplicates(
            subset=["season", "team", "player", "player_id"],
            keep="first",
        )

        season_text = str(season).strip()
        if len(season_text) == 4 and season_text.isdigit():
            ref_date = date(int(f"20{season_text[2:]}"), 6, 30)
        else:
            ref_date = date.today()

        profiles = fetch_player_ages(
            players["player_id"].dropna().astype(str).unique().tolist(),
            ref_date,
        )
        age_lookup = players.merge(profiles, how="left", on="player_id")

    print("ESPN summaries")
    espn.read_matchsheet()
    summary_root = Path(espn.data_dir)
    rows = []

    # read cached summary files
    for i, match in enumerate(schedule.itertuples(index=False), start=1):
        game_id = to_int(getattr(match, "game_id", None))
        if game_id is None:
            continue
        summary_file = summary_root / f"Summary_{game_id}.json"
        if summary_file.exists():
            with summary_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            rows.extend(parse_summary(payload, season, str(game_id)))

        if i == 1 or i % 25 == 0 or i == total_matches:
            print(f"ESPN summaries {i}/{total_matches}")

    if not rows:
        return pd.DataFrame(columns=ESPN_ANALYSIS_COLUMNS)

    # add age back onto match rows
    out = pd.DataFrame(rows)
    if not age_lookup.empty:
        age_lookup = age_lookup[["season", "team", "player", "player_id", "age_ref"]].copy()
        age_lookup["season"] = age_lookup["season"].astype(str)
        age_lookup["team"] = age_lookup["team"].astype(str)
        age_lookup["player"] = age_lookup["player"].astype(str)
        age_lookup["player_id"] = age_lookup["player_id"].astype(str)
        out["season"] = out["season"].astype(str)
        out["team"] = out["team"].astype(str)
        out["player"] = out["player"].astype(str)
        out["player_id"] = out["player_id"].astype(str)
        out = out.merge(
            age_lookup,
            how="left",
            on=["season", "team", "player", "player_id"],
        )
    else:
        out["age_ref"] = pd.NA

    out = out.rename(columns={"age_ref": "age"})
    # final order for the csv
    return out[ESPN_ANALYSIS_COLUMNS].sort_values(
        ["season", "game_id", "team", "player"],
        kind="stable",
    ).reset_index(drop=True)
