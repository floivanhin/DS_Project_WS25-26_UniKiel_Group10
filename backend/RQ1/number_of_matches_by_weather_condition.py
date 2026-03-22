"""
This script reads weather and match data from `combined_matches_weather.json`
and generates a chart showing the number of matches played under different weather conditions.

The weather descriptions are grouped into simplified categories in order to make
the analysis clearer and easier to interpret. For example, similar weather conditions
such as rain, drizzle, or showers are combined into a single category (`Rain`),
while overcast and cloudy conditions are grouped as `Cloudy`.

After categorizing the weather data, it counts how many matches were played
under each condition and visualizes the results in a chart.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
file_path = BASE_DIR / "combined_matches_weather.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

matches = data["matches"]
df = pd.json_normalize(matches)


def classify_weather(condition: str) -> str:
    if not isinstance(condition, str):
        return "Other"

    c = condition.lower()

    if "snow" in c:
        return "Snow"
    if "rain" in c or "drizzle" in c or "showers" in c:
        return "Rain"
    if "overcast" in c:
        return "Cloudy"
    if "cloud" in c:
        return "Cloudy"
    if "clear" in c:
        return "Clear"

    return "Other"


df["weather_group"] = df["weather.conditions"].apply(classify_weather)

weather_counts = (
    df["weather_group"]
    .value_counts()
    .reset_index()
)

weather_counts.columns = ["weather_group", "matches_count"]

print(weather_counts)

plt.figure(figsize=(8, 5))
sns.barplot(data=weather_counts, x="weather_group", y="matches_count")
plt.title("Number of matches by weather condition")
plt.xlabel("Weather condition")
plt.ylabel("Number of matches")
plt.tight_layout()
plt.show()