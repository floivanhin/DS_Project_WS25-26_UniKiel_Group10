import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

file_path = Path(__file__).resolve().parent / "capacity_cards_relation.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.json_normalize(data["matches"])

df = df.dropna(subset=["capacity", "cards_total"])

print(df[["venue_name", "capacity", "cards_total"]].head())

correlation = df["capacity"].corr(df["cards_total"])
print("Correlation:", correlation)


df_avg = (
    df.groupby("capacity")["cards_total"]
    .mean()
    .reset_index()
    .sort_values("capacity")
)

print(df_avg.head())

plt.figure(figsize=(8, 5))

sns.lineplot(data=df_avg, x="capacity", y="cards_total", marker="o")

plt.title("Average number of cards depending on arena capacity")
plt.xlabel("Arena capacity")
plt.ylabel("Average cards per match")

plt.tight_layout()
plt.show()