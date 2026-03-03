import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
if not WEATHER_API_KEY:
    raise RuntimeError("WEATHER_API_KEY is missing in .env")

WEATHER_BASE = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

DATE = "2026-03-02"

CITIES = [
    "Berlin",
    "Hamburg",
    "Munich",
    "Cologne",
    "Frankfurt",
    "Stuttgart",
    "Dusseldorf",
    "Leipzig",
    "Dortmund",
    "Bremen",
]

def main():
    out = {"date": DATE, "cities": {}}

    for city in CITIES:
        location = f"{city}, Germany"
        url = f"{WEATHER_BASE}/{requests.utils.quote(location)}/{DATE}"
        params = {
            "key": WEATHER_API_KEY,
            "unitGroup": "metric",
            "include": "days",       
            "contentType": "json",
        }

        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        day0 = (data.get("days") or [None])[0]
        if not day0:
            out["cities"][city] = {"error": "No daily data returned"}
            continue

        out["cities"][city] = {
            "resolvedAddress": data.get("resolvedAddress"),
            "lat": data.get("latitude"),
            "lon": data.get("longitude"),
            "temp": day0.get("temp"),
            "tempmax": day0.get("tempmax"),
            "tempmin": day0.get("tempmin"),
            "precip": day0.get("precip"),
            "windspeed": day0.get("windspeed"),
            "conditions": day0.get("conditions"),
        }

    with open(os.path.join(os.path.dirname(__file__), f"weather_{DATE}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved weather_{DATE}.json")

if __name__ == "__main__":
    main()