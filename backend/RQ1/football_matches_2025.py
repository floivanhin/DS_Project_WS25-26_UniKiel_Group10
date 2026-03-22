"""
This script sends API requests to retrieve information about all matches
in the German Bundesliga 2025 (1st division).

For each match, it collects relevant data such as participating teams,
match date, and the final result (e.g., goals scored by each team).

The script processes and structures the API responses into a consistent format.
All collected match data is then stored in a JSON file (`football.json`)
for further analysis and integration with other parts of the project.
"""

import os
import json

import requests
from dotenv import load_dotenv


load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY is missing in .env")

HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}
MATCHES_URL = "https://api.football-data.org/v4/competitions/BL1/matches"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "football.json")

SEASON = 2025


def fetch_matches(season: int) -> dict:
    params = {"season": season}
    response = requests.get(MATCHES_URL, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    data["_meta"] = {
        "season": season,
        "competitionCode": "BL1",
    }
    return data


def save_matches(data: dict, output_file: str = OUTPUT_FILE) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    data = fetch_matches(season=SEASON)
    save_matches(data)
    print(f"Saved {os.path.basename(OUTPUT_FILE)} for season {SEASON}")


if __name__ == "__main__":
    main()