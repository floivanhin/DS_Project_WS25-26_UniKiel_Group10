import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_2_API_KEY")
if not API_KEY:
    raise RuntimeError("FOOTBALL_2_API_KEY is missing in .env")

BASE = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

LEAGUE_ID = 78
SEASON = 2024

DATE_FROM = "2024-08-01"
DATE_TO   = "2024-09-01"

SLEEP_SECONDS = 7  # лимит 10 запросов/мин


def api_get(path: str, params: dict):
    url = f"{BASE}{path}"
    while True:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        errors = data.get("errors") or {}
        if errors:
            if "rateLimit" in errors:
                print("Rate limit reached, waiting 60 seconds...")
                time.sleep(60)
                continue
            raise RuntimeError(f"API errors for {path} {params}: {errors}")

        return data


def stat_value(stats_list, name: str):
    for item in stats_list:
        if item.get("type") == name:
            return item.get("value")
    return None


def to_int(x):
    if x is None:
        return 0
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        x = x.replace("%", "").strip()
        return int(x) if x.isdigit() else 0
    return 0


def main():
    # 1) fixtures -> games list
    fixtures_data = api_get(
        "/fixtures",
        {"league": LEAGUE_ID, "season": SEASON, "from": DATE_FROM, "to": DATE_TO},
    )
    fixtures = fixtures_data.get("response", [])
    print(f"Fixtures fetched: {len(fixtures)}")

    cards_out = []

    for i, fx in enumerate(fixtures, 1):
        fixture = fx.get("fixture") or {}
        teams = fx.get("teams") or {}

        fixture_id = fixture.get("id")
        match_name = f"{(teams.get('home') or {}).get('name')} vs {(teams.get('away') or {}).get('name')}"

        print(f"[{i}/{len(fixtures)}] Fetching cards for fixture={fixture_id}")

        stats_data = api_get("/fixtures/statistics", {"fixture": fixture_id})
        time.sleep(SLEEP_SECONDS)

        blocks = stats_data.get("response", [])

        home_id = (teams.get("home") or {}).get("id")
        away_id = (teams.get("away") or {}).get("id")

        def team_stats(team_id):
            for b in blocks:
                if (b.get("team") or {}).get("id") == team_id:
                    return b.get("statistics") or []
            return []

        home_stats = team_stats(home_id)
        away_stats = team_stats(away_id)

        home_y = to_int(stat_value(home_stats, "Yellow Cards"))
        home_r = to_int(stat_value(home_stats, "Red Cards"))
        away_y = to_int(stat_value(away_stats, "Yellow Cards"))
        away_r = to_int(stat_value(away_stats, "Red Cards"))

        cards_out.append({
            "fixture_id": fixture_id,
            "date": fixture.get("date"),
            "match": match_name,
            "yellow_home": home_y,
            "red_home": home_r,
            "yellow_away": away_y,
            "red_away": away_r,
            "yellow_total": home_y + away_y,
            "red_total": home_r + away_r,
            "cards_total": home_y + home_r + away_y + away_r,
        })

    out = {
        "_meta": {
            "league": "Bundesliga",
            "league_id": LEAGUE_ID,
            "season": SEASON,
            "dateFrom": DATE_FROM,
            "dateTo": DATE_TO,
            "matches": len(cards_out),
        },
        "matches": cards_out,
    }

    output_path = os.path.join(os.path.dirname(__file__), "cards.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()