import os
import json
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY is missing in .env")

headers = {"X-Auth-Token": FOOTBALL_API_KEY}

today = date.today()
date_from = (today - timedelta(days=7)).isoformat()
date_to = today.isoformat()

url = "https://api.football-data.org/v4/competitions/BL1/matches"
params = {"dateFrom": date_from, "dateTo": date_to}

r = requests.get(url, headers=headers, params=params, timeout=30)
r.raise_for_status()
data = r.json()

data["_meta"] = {"dateFrom": date_from, "dateTo": date_to}

with open(os.path.join(os.path.dirname(__file__), "football.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved football.json")