import json
import pandas as pd
from pathlib import Path

from dash import Dash, html, dcc
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent
file_path = BASE_DIR / "capacity_cards_relation.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.json_normalize(data["matches"])

df = df.dropna(subset=["capacity", "cards_total"])

correlation = df["capacity"].corr(df["cards_total"])

df_avg = (
    df.groupby("capacity")["cards_total"]
    .mean()
    .reset_index()
    .sort_values("capacity")
)

fig_avg = px.line(
    df_avg,
    x="capacity",
    y="cards_total",
    markers=True,
    title="Average cards depending on arena capacity",
)

fig_avg.update_layout(template="plotly_white")

fig_scatter = px.scatter(
    df,
    x="capacity",
    y="cards_total",
    title="Cards per match vs arena capacity",
    opacity=0.7,
)

fig_scatter.update_layout(template="plotly_white")


app = Dash(__name__)
server = app.server

app.layout = html.Div(
    style={
        "backgroundColor": "#f5f6f8",
        "minHeight": "100vh",
        "padding": "40px",
        "fontFamily": "Arial",
    },
    children=[

        html.H1(
            "Research Question",
            style={"textAlign": "center"}
        ),

        html.H3(
            "How does stadium capacity influence the number of cards in a match?",
            style={"textAlign": "center", "marginBottom": "40px"}
        ),

        html.Div(
            [
                html.P(f"Matches analyzed: {len(df)}"),
                html.P(f"Correlation (capacity vs cards): {round(correlation, 3)}"),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "10px",
                "marginBottom": "30px",
                "width": "400px",
                "margin": "0 auto 30px auto",
                "textAlign": "center",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            }
        ),

        html.Div(
            [
                dcc.Graph(figure=fig_avg),
                dcc.Graph(figure=fig_scatter),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "10px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            }
        ),
    ],
)

if __name__ == "__main__":
    app.run(debug=True)