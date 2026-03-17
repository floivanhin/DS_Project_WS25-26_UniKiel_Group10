from pathlib import Path
import json

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "combined_matches_weather.json"


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


def load_dataframe() -> pd.DataFrame:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = data.get("matches", [])
    df = pd.json_normalize(matches)

    if df.empty:
        return df

    df["weather_group"] = df["weather.conditions"].apply(classify_weather)
    df["total_goals"] = (
        pd.to_numeric(df.get("score.fullTime.home"), errors="coerce").fillna(0)
        + pd.to_numeric(df.get("score.fullTime.away"), errors="coerce").fillna(0)
    )

    if "utcDate" in df.columns:
        df["utcDate"] = pd.to_datetime(df["utcDate"], errors="coerce")

    return df


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    order = ["Clear", "Cloudy", "Rain", "Snow", "Other"]

    summary = (
        df.groupby("weather_group", dropna=False)
        .agg(
            avg_goals=("total_goals", "mean"),
            match_count=("total_goals", "size"),
            median_goals=("total_goals", "median"),
        )
        .reset_index()
    )

    summary["weather_group"] = pd.Categorical(
        summary["weather_group"], categories=order, ordered=True
    )
    summary = summary.sort_values("weather_group")
    return summary


def create_bar_chart(summary: pd.DataFrame):
    fig = px.bar(
        summary,
        x="weather_group",
        y="avg_goals",
        text=summary["avg_goals"].round(2),
        custom_data=["match_count", "median_goals"],
        title="Average total goals by weather condition",
        labels={
            "weather_group": "Weather condition",
            "avg_goals": "Average total goals",
        },
    )

    fig.update_traces(
        hovertemplate=(
            "Weather: %{x}<br>"
            "Average goals: %{y:.2f}<br>"
            "Matches: %{customdata[0]}<br>"
            "Median goals: %{customdata[1]:.2f}<extra></extra>"
        )
    )
    fig.update_layout(template="plotly_white")
    return fig


def create_distribution_chart(filtered_df: pd.DataFrame):
    dist = (
        filtered_df.groupby("total_goals")
        .size()
        .reset_index(name="match_count")
        .sort_values("total_goals")
    )

    fig = px.bar(
        dist,
        x="total_goals",
        y="match_count",
        title="Distribution of total goals",
        labels={
            "total_goals": "Total goals in a match",
            "match_count": "Number of matches",
        },
    )
    fig.update_layout(template="plotly_white")
    return fig


df = load_dataframe()
summary_df = build_summary(df) if not df.empty else pd.DataFrame()

app = Dash(__name__)
server = app.server

available_weather = summary_df["weather_group"].astype(str).tolist() if not summary_df.empty else []

app.layout = html.Div(
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "24px", "fontFamily": "Arial"},
    children=[
        html.H1("How do weather conditions influence total goals scored?"),
        html.P(
            "Bundesliga matches are grouped by simplified weather categories. "
            "The dashboard compares average total goals and shows how many matches belong to each group."
        ),
        html.Div(
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "20px"},
            children=[
                html.Div(
                    [html.H3("Weather filter"),
                     dcc.Dropdown(
                         id="weather-filter",
                         options=[{"label": "All", "value": "All"}] + [
                             {"label": w, "value": w} for w in available_weather
                         ],
                         value="All",
                         clearable=False,
                     )],
                    style={"flex": "1", "minWidth": "260px"},
                ),
                html.Div(
                    [html.H3("Metric"),
                     dcc.RadioItems(
                         id="metric-selector",
                         options=[
                             {"label": "Average goals", "value": "avg_goals"},
                             {"label": "Median goals", "value": "median_goals"},
                             {"label": "Match count", "value": "match_count"},
                         ],
                         value="avg_goals",
                         inline=True,
                     )],
                    style={"flex": "2", "minWidth": "320px"},
                ),
            ],
        ),
        html.Div(id="summary-text", style={"marginBottom": "16px", "fontWeight": "bold"}),
        dcc.Graph(id="main-chart"),
        dcc.Graph(id="distribution-chart"),
        html.H3("Summary table"),
        html.Div(id="summary-table"),
    ],
)


@app.callback(
    Output("summary-text", "children"),
    Output("main-chart", "figure"),
    Output("distribution-chart", "figure"),
    Output("summary-table", "children"),
    Input("weather-filter", "value"),
    Input("metric-selector", "value"),
)
def update_dashboard(selected_weather: str, selected_metric: str):
    filtered_df = df.copy()

    if selected_weather != "All":
        filtered_df = filtered_df[filtered_df["weather_group"] == selected_weather]

    filtered_summary = build_summary(filtered_df)

    metric_labels = {
        "avg_goals": "Average total goals",
        "median_goals": "Median total goals",
        "match_count": "Number of matches",
    }

    fig = px.bar(
        filtered_summary,
        x="weather_group",
        y=selected_metric,
        text=filtered_summary[selected_metric].round(2) if selected_metric != "match_count" else filtered_summary[selected_metric],
        custom_data=["match_count", "avg_goals", "median_goals"],
        title=f"{metric_labels[selected_metric]} by weather condition",
        labels={
            "weather_group": "Weather condition",
            selected_metric: metric_labels[selected_metric],
        },
    )
    fig.update_traces(
        hovertemplate=(
            "Weather: %{x}<br>"
            "Matches: %{customdata[0]}<br>"
            "Average goals: %{customdata[1]:.2f}<br>"
            "Median goals: %{customdata[2]:.2f}<extra></extra>"
        )
    )
    fig.update_layout(template="plotly_white")

    dist_fig = create_distribution_chart(filtered_df)

    total_matches = len(filtered_df)
    avg_goals = filtered_df["total_goals"].mean() if total_matches else 0
    summary_text = (
        f"Current selection: {selected_weather}. "
        f"Matches: {total_matches}. "
        f"Average total goals: {avg_goals:.2f}."
    )

    table = html.Table(
        style={"width": "100%", "borderCollapse": "collapse"},
        children=[
            html.Thead(
                html.Tr([
                    html.Th("Weather group", style={"textAlign": "left", "padding": "8px", "borderBottom": "1px solid #ccc"}),
                    html.Th("Average goals", style={"textAlign": "left", "padding": "8px", "borderBottom": "1px solid #ccc"}),
                    html.Th("Median goals", style={"textAlign": "left", "padding": "8px", "borderBottom": "1px solid #ccc"}),
                    html.Th("Matches", style={"textAlign": "left", "padding": "8px", "borderBottom": "1px solid #ccc"}),
                ])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(str(row["weather_group"]), style={"padding": "8px", "borderBottom": "1px solid #eee"}),
                    html.Td(f'{row["avg_goals"]:.2f}', style={"padding": "8px", "borderBottom": "1px solid #eee"}),
                    html.Td(f'{row["median_goals"]:.2f}', style={"padding": "8px", "borderBottom": "1px solid #eee"}),
                    html.Td(str(int(row["match_count"])), style={"padding": "8px", "borderBottom": "1px solid #eee"}),
                ])
                for _, row in filtered_summary.iterrows()
            ])
        ],
    )

    return summary_text, fig, dist_fig, table


if __name__ == "__main__":
    app.run(debug=True)
