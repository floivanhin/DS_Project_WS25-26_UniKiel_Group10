import os
import json
from datetime import date, timedelta

import requests
from dotenv import load_dotenv


load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY is missing in .env")

HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}
MATCHES_URL = "https://api.football-data.org/v4/competitions/BL1/matches"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "football.json")


def fetch_matches(date_from: str, date_to: str) -> dict:
    params = {"dateFrom": date_from, "dateTo": date_to}
    response = requests.get(MATCHES_URL, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    data["_meta"] = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "competitionCode": "BL1",
    }
    return data


def save_matches(data: dict, output_file: str = OUTPUT_FILE) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    today = date.today()
    date_from = (today - timedelta(days=7)).isoformat()
    date_to = today.isoformat()

    data = fetch_matches(date_from=date_from, date_to=date_to)
    save_matches(data)
    print(f"Saved {os.path.basename(OUTPUT_FILE)} for {date_from} -> {date_to}")


if __name__ == "__main__":
    main()