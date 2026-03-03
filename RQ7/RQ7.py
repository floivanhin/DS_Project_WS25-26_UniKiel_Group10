import json
import os
import time
import requests

API_KEY = "c1efa65f1ef945fb99d5cf6c23acc446"
headers = {"X-Auth-Token": API_KEY}

with open("football.json", "r", encoding="utf-8") as f:
    data = json.load(f)

match_ids = [m["id"] for m in data["matches"]]

details = []
for i, mid in enumerate(match_ids, 1):
    print(f"[{i}/{len(match_ids)}] Fetching match {mid}...")
    r = requests.get(f"https://api.football-data.org/v4/matches/{mid}", headers=headers)
    r.raise_for_status()
    details.append(r.json())

    time.sleep(6)  

with open(os.path.join(os.path.dirname(__file__), "football_detailed.json"), "w", encoding="utf-8") as f:
    json.dump(details, f, indent=2, ensure_ascii=False)

print("Saved football_detailed.json")