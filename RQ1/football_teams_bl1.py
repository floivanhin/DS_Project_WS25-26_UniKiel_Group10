import os
import json

import requests
from dotenv import load_dotenv


load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY is missing in .env")

HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}
TEAMS_URL = "https://api.football-data.org/v4/competitions/BL1/teams"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "teams.json")


def fetch_teams() -> dict:
    response = requests.get(TEAMS_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def save_teams(data: dict, output_file: str = OUTPUT_FILE) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    data = fetch_teams()
    save_teams(data)
    print(f"Saved {os.path.basename(OUTPUT_FILE)}")


if __name__ == "__main__":
    main()