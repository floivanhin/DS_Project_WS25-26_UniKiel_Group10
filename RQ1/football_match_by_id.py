import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY is missing in .env")

headers = {"X-Auth-Token": FOOTBALL_API_KEY}

MATCH_ID = 540621  # <-- id from football.json

url = f"https://api.football-data.org/v4/matches/{MATCH_ID}"

r = requests.get(url, headers=headers, timeout=30)
r.raise_for_status()
data = r.json()

with open(os.path.join(os.path.dirname(__file__), f"match_{MATCH_ID}.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Saved match_{MATCH_ID}.json")