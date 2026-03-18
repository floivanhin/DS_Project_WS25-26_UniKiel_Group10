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

            if "requests" in errors:
                raise RuntimeError(
                    f"Daily request limit reached for {path} {params}: {errors}"
                )

            raise RuntimeError(f"API errors for {path} {params}: {errors}")

        return data


def main():
    print(f"Fetching teams for league={LEAGUE_ID}, season={SEASON} ...")
    teams_data = api_get(
        "/teams",
        {
            "league": LEAGUE_ID,
            "season": SEASON,
        },
    )

    response = teams_data.get("response", [])
    print(f"Teams fetched: {len(response)}")

    venues_out = []
    seen_venue_ids = set()

    for i, item in enumerate(response, 1):
        team = item.get("team") or {}
        venue = item.get("venue") or {}

        team_name = team.get("name")
        venue_id = venue.get("id")

        print(f"[{i}/{len(response)}] Team: {team_name} | venue_id={venue_id}")

        if venue_id is None:
            print("  -> skipped: venue_id is missing")
            continue

        if venue_id in seen_venue_ids:
            print("  -> skipped: venue already saved")
            continue

        seen_venue_ids.add(venue_id)

        venues_out.append(
            {
                "venue_id": venue_id,
                "team_name": team_name,
                "name": venue.get("name"),
                "address": venue.get("address"),
                "city": venue.get("city"),
                "capacity": venue.get("capacity"),
                "surface": venue.get("surface"),
                "image": venue.get("image"),
            }
        )

    venues_out.sort(key=lambda x: (x["team_name"] or "", x["venue_id"] or 0))

    missing_capacity = sum(1 for v in venues_out if v.get("capacity") is None)

    out = {
        "_meta": {
            "league": "Bundesliga",
            "league_id": LEAGUE_ID,
            "season": SEASON,
            "teams": len(response),
            "venues": len(venues_out),
            "missing_capacity": missing_capacity,
            "source": "/teams",
        },
        "venues": venues_out,
    }

    output_path = os.path.join(os.path.dirname(__file__), "capacity.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved: {output_path}")
    print(f"Unique venues saved: {len(venues_out)}")
    print(f"Venues with missing capacity: {missing_capacity}")


if __name__ == "__main__":
    main()