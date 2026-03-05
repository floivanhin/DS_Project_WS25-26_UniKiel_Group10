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

SLEEP_SECONDS = 7 


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


def main():
    # 1) fixtures -> venue_id
    fixtures_data = api_get(
        "/fixtures",
        {"league": LEAGUE_ID, "season": SEASON, "from": DATE_FROM, "to": DATE_TO},
    )
    fixtures = fixtures_data.get("response", [])
    print(f"Fixtures fetched: {len(fixtures)}")

    venue_ids = []
    seen = set()
    for fx in fixtures:
        venue = (fx.get("fixture") or {}).get("venue") or {}
        vid = venue.get("id")
        if vid and vid not in seen:
            seen.add(vid)
            venue_ids.append(vid)

    print(f"Unique venues: {len(venue_ids)}")

    # 2) venues -> capacity
    venues_out = []
    for i, vid in enumerate(venue_ids, 1):
        print(f"[{i}/{len(venue_ids)}] Fetching venue id={vid}")
        vdata = api_get("/venues", {"id": vid})
        time.sleep(SLEEP_SECONDS)

        resp = vdata.get("response", [])
        v = resp[0] if resp else {}

        venues_out.append({
            "venue_id": v.get("id", vid),
            "name": v.get("name"),
            "city": v.get("city"),
            "capacity": v.get("capacity"),
        })

    out = {
        "_meta": {
            "league": "Bundesliga",
            "league_id": LEAGUE_ID,
            "season": SEASON,
            "dateFrom": DATE_FROM,
            "dateTo": DATE_TO,
            "venues": len(venues_out),
        },
        "venues": venues_out,
    }

    output_path = os.path.join(os.path.dirname(__file__), "capacity.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()