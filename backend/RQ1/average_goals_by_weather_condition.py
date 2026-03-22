"""
This script reads combined match and weather data from `combined_matches_weather.json`
and generates a chart showing how the number of goals scored in matches
varies under different weather conditions.

The weather descriptions are first categorized into simplified groups
(e.g., `Rain`, `Snow`, `Cloudy`, `Clear`) to make the analysis more interpretable.

For each weather category, the script calculates the total or average number of goals
scored in matches played under those conditions.

The aggregated results are then visualized in a chart to highlight potential
relationships between weather conditions and goal scoring.
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

df["total_goals"] = (
    df["score.fullTime.home"].fillna(0) +
    df["score.fullTime.away"].fillna(0)
)

goals_by_weather = (
    df.groupby("weather_group")["total_goals"]
    .mean()
    .reset_index()
)

print(goals_by_weather)

plt.figure(figsize=(8, 5))
sns.barplot(data=goals_by_weather, x="weather_group", y="total_goals")

plt.title("Average goals by weather condition")
plt.xlabel("Weather condition")
plt.ylabel("Average goals")

plt.tight_layout()
plt.show()