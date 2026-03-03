import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY is missing in .env")

headers = {"X-Auth-Token": FOOTBALL_API_KEY}

url = "https://api.football-data.org/v4/competitions/BL1/teams"

r = requests.get(url, headers=headers, timeout=30)
r.raise_for_status()
data = r.json()

with open(os.path.join(os.path.dirname(__file__), "teams.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved teams.json")