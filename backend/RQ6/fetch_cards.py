"""
This script sends API requests to retrieve match data with a focus on
yellow and red cards issued during Bundesliga games.

For each match, it collects information about the number of yellow and red cards,
along with basic match metadata, and stores the results in `cards.json`.

Due to the API request limit (100 requests per day), the script is designed
to process data in batches. It performs up to 90 requests per run to stay
within safe limits.

The script supports incremental data collection:
if `cards.json` already exists, it will append new data without overwriting
previous results. This allows the script to be executed again on the next day
to continue fetching the remaining matches.

This approach ensures that the full dataset can be built over multiple runs
while respecting API rate limits.
"""

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

SLEEP_SECONDS = 7
SAVE_EVERY = 1

MAX_REQUESTS_PER_RUN = 90

BASE_DIR = os.path.dirname(__file__)
OUTPUT_FILE = os.path.join(BASE_DIR, "cards.json")
FIXTURES_CACHE_FILE = os.path.join(BASE_DIR, "fixtures_cache.json")


class DailyRequestLimitReached(Exception):
    pass


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def api_get(path: str, params: dict):
    url = f"{BASE}{path}"

    while True:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        errors = data.get("errors") or {}
        if errors:
            if "rateLimit" in errors:
                print("Minute rate limit reached, waiting 60 seconds...")
                time.sleep(60)
                continue

            if "requests" in errors:
                raise DailyRequestLimitReached(errors["requests"])

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


def load_fixtures():
    cached = load_json(FIXTURES_CACHE_FILE, None)
    if cached:
        fixtures = cached.get("response", [])
        print(f"Fixtures loaded from cache: {len(fixtures)}")
        return cached

    fixtures_data = api_get("/fixtures", {"league": LEAGUE_ID, "season": SEASON})
    save_json(FIXTURES_CACHE_FILE, fixtures_data)

    fixtures = fixtures_data.get("response", [])
    print(f"Fixtures fetched from API: {len(fixtures)}")
    return fixtures_data


def load_existing_output():
    existing = load_json(
        OUTPUT_FILE,
        {
            "_meta": {
                "league": "Bundesliga",
                "league_id": LEAGUE_ID,
                "season": SEASON,
                "matches": 0,
                "last_run_new_requests": 0,
                "total_saved_matches": 0,
            },
            "matches": [],
        },
    )

    processed_ids = {
        match.get("fixture_id")
        for match in existing.get("matches", [])
        if match.get("fixture_id") is not None
    }

    return existing, processed_ids


def save_progress(out: dict, last_run_new_requests: int = 0) -> None:
    out.setdefault("_meta", {})
    out["_meta"]["matches"] = len(out.get("matches", []))
    out["_meta"]["total_saved_matches"] = len(out.get("matches", []))
    out["_meta"]["last_run_new_requests"] = last_run_new_requests

    save_json(OUTPUT_FILE, out)
    print(f"Progress saved: {len(out.get('matches', []))} matches -> {OUTPUT_FILE}")


def main():
    fixtures_data = load_fixtures()
    fixtures = fixtures_data.get("response", [])

    existing_out, processed_ids = load_existing_output()
    cards_out = existing_out["matches"]  # именно ссылка на тот же список

    total = len(fixtures)
    new_requests_made = 0

    print(f"Total fixtures in season: {total}")
    print(f"Already processed: {len(processed_ids)}")
    print(f"Remaining: {total - len(processed_ids)}")
    print(f"Max new requests this run: {MAX_REQUESTS_PER_RUN}")

    try:
        for i, fx in enumerate(fixtures, 1):
            fixture = fx.get("fixture") or {}
            teams = fx.get("teams") or {}
            venue = fixture.get("venue") or {}

            fixture_id = fixture.get("id")
            if fixture_id in processed_ids:
                print(f"[{i}/{total}] Skipping already saved fixture={fixture_id}")
                continue

            if new_requests_made >= MAX_REQUESTS_PER_RUN:
                print("\nReached local per-run request limit.")
                save_progress(existing_out, last_run_new_requests=new_requests_made)
                print("Stop now. Run the script again tomorrow to continue.")
                return

            venue_id = venue.get("id")
            home_name = (teams.get("home") or {}).get("name")
            away_name = (teams.get("away") or {}).get("name")
            match_name = f"{home_name} vs {away_name}"

            print(
                f"[{i}/{total}] "
                f"Fetching cards for fixture={fixture_id} ({match_name}) "
                f"| new requests this run: {new_requests_made + 1}/{MAX_REQUESTS_PER_RUN}"
            )

            stats_data = api_get("/fixtures/statistics", {"fixture": fixture_id})
            new_requests_made += 1

            blocks = stats_data.get("response", [])
            home_id = (teams.get("home") or {}).get("id")
            away_id = (teams.get("away") or {}).get("id")

            def team_stats(team_id):
                for block in blocks:
                    if (block.get("team") or {}).get("id") == team_id:
                        return block.get("statistics") or []
                return []

            home_stats = team_stats(home_id)
            away_stats = team_stats(away_id)

            home_y = to_int(stat_value(home_stats, "Yellow Cards"))
            home_r = to_int(stat_value(home_stats, "Red Cards"))
            away_y = to_int(stat_value(away_stats, "Yellow Cards"))
            away_r = to_int(stat_value(away_stats, "Red Cards"))

            cards_out.append(
                {
                    "fixture_id": fixture_id,
                    "venue_id": venue_id,
                    "date": fixture.get("date"),
                    "match": match_name,
                    "yellow_home": home_y,
                    "red_home": home_r,
                    "yellow_away": away_y,
                    "red_away": away_r,
                    "yellow_total": home_y + away_y,
                    "red_total": home_r + away_r,
                    "cards_total": home_y + home_r + away_y + away_r,
                }
            )
            processed_ids.add(fixture_id)

            if len(cards_out) % SAVE_EVERY == 0:
                save_progress(existing_out, last_run_new_requests=new_requests_made)

            time.sleep(SLEEP_SECONDS)

    except DailyRequestLimitReached as exc:
        save_progress(existing_out, last_run_new_requests=new_requests_made)
        print("\nDaily request limit reached.")
        print(str(exc))
        print("Run this script again tomorrow — it will continue from the saved progress.")
        return

    save_progress(existing_out, last_run_new_requests=new_requests_made)
    print("Done.")


if __name__ == "__main__":
    main()