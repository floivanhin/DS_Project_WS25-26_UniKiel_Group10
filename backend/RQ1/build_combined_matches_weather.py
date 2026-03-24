"""
This script combines match data and team data into a single dataset.

It reads data from:
- `football.json` (match information and results)
- `teams.json` (team and squad data)

The script matches teams to their corresponding matches and merges
the relevant information into a unified structure.

The resulting combined dataset is saved to `combined_matches_weather.json`,
which is later used for analysis and visualization.
"""


import os
import json

from football_matches_2025 import fetch_matches, save_matches
from football_teams_bl1 import fetch_teams, save_teams
from weather_for_matches import build_matches_weather


BASE_DIR = os.path.dirname(__file__)

MATCHES_FILE = os.path.join(BASE_DIR, "football.json")
TEAMS_FILE = os.path.join(BASE_DIR, "teams.json")
COMBINED_FILE = os.path.join(BASE_DIR, "combined_matches_weather.json")

SEASON = 2025


def main() -> None:

    matches_data = fetch_matches(SEASON)
    save_matches(matches_data, MATCHES_FILE)

    teams_data = fetch_teams()
    save_teams(teams_data, TEAMS_FILE)

    combined_data = build_matches_weather(matches_data, teams_data)

    with open(COMBINED_FILE, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    print(f"Saved {os.path.basename(COMBINED_FILE)}")


if __name__ == "__main__":
    main()