import json
import time
import requests

API_KEY = "__"

headers = {"X-Auth-Token": API_KEY}

url = "https://api.football-data.org/v4/competitions/BL1/teams"

r = requests.get(url, headers=headers)

data = r.json()

with open("teams.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

print("Saved teams.json")