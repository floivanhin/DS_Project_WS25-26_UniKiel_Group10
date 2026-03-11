import os
import json
from datetime import datetime

import requests
from dotenv import load_dotenv


load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
if not WEATHER_API_KEY:
    raise RuntimeError("WEATHER_API_KEY is missing in .env")

BASE_DIR = os.path.dirname(__file__)
WEATHER_BASE = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
MATCHES_FILE = os.path.join(BASE_DIR, "football.json")
TEAMS_FILE = os.path.join(BASE_DIR, "teams.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "matches_weather.json")


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_city_from_address(address: str) -> str | None:
    if not address:
        return None

    parts = address.split()
    if len(parts) < 2:
        return address.strip() or None

    city_parts = []
    seen_postcode = False

    for token in reversed(parts):
        if token.isdigit() and len(token) == 5:
            seen_postcode = True
            continue
        if seen_postcode:
            city_parts.append(token)
        elif not city_parts:
            continue
        else:
            break

    if city_parts:
        return " ".join(reversed(city_parts)).strip()

    return address.strip() or None


def build_team_lookup(teams_data: dict) -> dict[int, dict]:
    lookup = {}

    for team in teams_data.get("teams", []):
        address = team.get("address")
        city = extract_city_from_address(address)
        lookup[team["id"]] = {
            "teamId": team.get("id"),
            "teamName": team.get("name"),
            "shortName": team.get("shortName"),
            "venue": team.get("venue"),
            "address": address,
            "city": city,
        }

    return lookup


def get_match_date(match: dict) -> str:
    return datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00")).date().isoformat()


def fetch_weather_for_address(address: str, match_date: str) -> dict:
    location = f"{address}, Germany"
    url = f"{WEATHER_BASE}/{requests.utils.quote(location)}/{match_date}"
    params = {
        "key": WEATHER_API_KEY,
        "unitGroup": "metric",
        "include": "days",
        "contentType": "json",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    day0 = (data.get("days") or [None])[0]
    if not day0:
        raise RuntimeError(f"No weather data returned for {location} on {match_date}")

    return {
        "requestedAddress": address,
        "resolvedAddress": data.get("resolvedAddress"),
        "lat": data.get("latitude"),
        "lon": data.get("longitude"),
        "temp": day0.get("temp"),
        "tempmax": day0.get("tempmax"),
        "tempmin": day0.get("tempmin"),
        "precip": day0.get("precip"),
        "windspeed": day0.get("windspeed"),
        "conditions": day0.get("conditions"),
    }


def build_matches_weather(matches_data: dict, teams_data: dict) -> dict:
    team_lookup = build_team_lookup(teams_data)
    out = {
        "_meta": matches_data.get("_meta", {}),
        "competition": matches_data.get("competition", {}),
        "matches": [],
    }

    for match in matches_data.get("matches", []):
        home_team_id = match.get("homeTeam", {}).get("id")
        home_team_info = team_lookup.get(home_team_id)

        if not home_team_info:
            out["matches"].append({
                "matchId": match.get("id"),
                "error": f"Home team with id {home_team_id} not found in teams.json",
            })
            continue

        address = home_team_info.get("address")
        match_date = get_match_date(match)

        if not address:
            out["matches"].append({
                "matchId": match.get("id"),
                "error": f"No address found for home team {home_team_info.get('teamName')}",
            })
            continue

        try:
            weather = fetch_weather_for_address(address=address, match_date=match_date)
        except requests.HTTPError as exc:
            out["matches"].append({
                "matchId": match.get("id"),
                "homeTeam": home_team_info,
                "matchDate": match_date,
                "error": f"Weather request failed: {exc}",
            })
            continue

        out["matches"].append({
            "matchId": match.get("id"),
            "utcDate": match.get("utcDate"),
            "matchDate": match_date,
            "status": match.get("status"),
            "matchday": match.get("matchday"),
            "homeTeam": home_team_info,
            "awayTeam": match.get("awayTeam", {}),
            "score": match.get("score", {}),
            "weather": weather,
        })

    return out


def save_output(data: dict, output_file: str = OUTPUT_FILE) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    matches_data = load_json(MATCHES_FILE)
    teams_data = load_json(TEAMS_FILE)
    combined_weather = build_matches_weather(matches_data, teams_data)
    save_output(combined_weather)
    print(f"Saved {os.path.basename(OUTPUT_FILE)}")


if __name__ == "__main__":
    main()