import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_2_API_KEY")
if not API_KEY:
    raise RuntimeError("FOOTBALL_2_API_KEY is missing in .env")

HEADERS = {"x-apisports-key": API_KEY}

BASE = "https://v3.football.api-sports.io"

# Bundesliga
LEAGUE_ID = 78
SEASON = 2024

DATE_FROM = "2024-08-01"
DATE_TO   = "2024-09-01"

MAX_FIXTURES = 30          
SLEEP_SECONDS = 1.0        


def api_get(path: str, params: dict):
    url = f"{BASE}{path}"

    while True:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        if data.get("errors"):
            if "rateLimit" in data["errors"]:
                print("Rate limit reached, waiting 60 seconds...")
                time.sleep(60)
                continue
            else:
                raise RuntimeError(f"API errors for {path} {params}: {data['errors']}")

        return data


def extract_stat(stats_list, stat_type: str):
    """stats_list = [{'type': 'Fouls', 'value': 11}, ...]"""
    for item in stats_list:
        if item.get("type") == stat_type:
            return item.get("value")
    return None


def to_int(value):
    """API иногда даёт None, иногда строку, иногда число."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.replace("%", "").strip()
        if value.isdigit():
            return int(value)
    return 0


def main():
    fixtures_data = api_get(
        "/fixtures",
        {
            "league": LEAGUE_ID,
            "season": SEASON,
            "from": DATE_FROM,
            "to": DATE_TO,
        },
    )

    fixtures = fixtures_data.get("response", [])
    if MAX_FIXTURES is not None:
        fixtures = fixtures[:MAX_FIXTURES]

    venue_cache = {}

    out = {
        "_meta": {
            "league": "Bundesliga",
            "league_id": LEAGUE_ID,
            "season": SEASON,
            "dateFrom": DATE_FROM,
            "dateTo": DATE_TO,
            "fixtures_fetched": len(fixtures),
            "note": "Cards from /fixtures/statistics, venue capacity from /venues.",
        },
        "matches": [],
    }

    for i, fx in enumerate(fixtures, start=1):
        fixture = fx.get("fixture", {})
        teams = fx.get("teams", {})

        fixture_id = fixture.get("id")
        venue = fixture.get("venue") or {}
        venue_id = venue.get("id")

        print(f"[{i}/{len(fixtures)}] fixture={fixture_id}, venue_id={venue_id}")

        # 2) Statistics for the match (cards/fouls)
        stats_data = api_get("/fixtures/statistics", {"fixture": fixture_id})
        time.sleep(SLEEP_SECONDS)

        # response: [{team:{...}, statistics:[...]}, {team:{...}, statistics:[...]}]
        stats_blocks = stats_data.get("response", [])

        home_team = teams.get("home", {})
        away_team = teams.get("away", {})

        def find_team_stats(team_id):
            for b in stats_blocks:
                if (b.get("team") or {}).get("id") == team_id:
                    return b.get("statistics") or []
            return []

        home_stats = find_team_stats(home_team.get("id"))
        away_stats = find_team_stats(away_team.get("id"))

        home_yellow = to_int(extract_stat(home_stats, "Yellow Cards"))
        home_red = to_int(extract_stat(home_stats, "Red Cards"))
        home_fouls = to_int(extract_stat(home_stats, "Fouls"))

        away_yellow = to_int(extract_stat(away_stats, "Yellow Cards"))
        away_red = to_int(extract_stat(away_stats, "Red Cards"))
        away_fouls = to_int(extract_stat(away_stats, "Fouls"))

        # 3) Capacity through /venues?id=
        capacity = None
        venue_details = None

        if venue_id:
            if venue_id in venue_cache:
                venue_details = venue_cache[venue_id]
            else:
                vdata = api_get("/venues", {"id": venue_id})
                time.sleep(SLEEP_SECONDS)
                resp = vdata.get("response", [])
                venue_details = resp[0] if resp else None
                venue_cache[venue_id] = venue_details

            if isinstance(venue_details, dict):
                capacity = venue_details.get("capacity")

        match_record = {
            "fixture_id": fixture_id,
            "date": fixture.get("date"),
            "referee": fixture.get("referee"),
            "round": (fx.get("league") or {}).get("round"),

            "home": {"id": home_team.get("id"), "name": home_team.get("name")},
            "away": {"id": away_team.get("id"), "name": away_team.get("name")},

            "venue": {
                "id": venue_id,
                "name": venue.get("name"),
                "city": venue.get("city"),
                "capacity": capacity,
            },

            "stats_home": {
                "fouls": home_fouls,
                "yellow": home_yellow,
                "red": home_red,
                "cards_total": home_yellow + home_red,
                "cards_per_foul": (home_yellow + home_red) / home_fouls if home_fouls else None,
            },
            "stats_away": {
                "fouls": away_fouls,
                "yellow": away_yellow,
                "red": away_red,
                "cards_total": away_yellow + away_red,
                "cards_per_foul": (away_yellow + away_red) / away_fouls if away_fouls else None,
            },
        }

        out["matches"].append(match_record)

    output_path = os.path.join(os.path.dirname(__file__), "rq7_cards_capacity.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()