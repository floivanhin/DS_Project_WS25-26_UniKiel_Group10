import os, json, requests
from dotenv import load_dotenv

load_dotenv()

KEY = os.getenv("FOOTBALL_2_API_KEY")
if not KEY:
    raise RuntimeError("FOOTBALL_2_API_KEY is missing in .env")

url = "https://v3.football.api-sports.io/fixtures"
headers = {"x-apisports-key": KEY}
params = {"league": 78, "season": 2024}

r = requests.get(url, headers=headers, params=params, timeout=30)
r.raise_for_status()
data = r.json()

data["_meta"] = {"league": "Bundesliga", "season": 2024}

with open(os.path.join(os.path.dirname(__file__), "football.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved football.json")