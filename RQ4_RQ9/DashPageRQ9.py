# Import packages
from pathlib import Path

from dash import Dash, Input, Output, callback, dcc, html
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# These paths make the script independent from the current working directory.
BASE_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = BASE_DIR / "analysis_output" / "rq9"
RAW_DATA_PATH = (
    BASE_DIR
    / "data"
    / "downloaded_outputs_to_analyse"
    / "espn_player_match_data_for_rq9.csv"
)

# Load the summary tables for team-level charts and the raw ESPN file for the
# dynamic age-profile calculation.
season_age_df = pd.read_csv(ANALYSIS_DIR / "bundesliga_season_age_summary.csv")
team_efficiency_df = pd.read_csv(ANALYSIS_DIR / "rq9_team_age_vs_efficiency.csv")
optimal_age_df = pd.read_csv(ANALYSIS_DIR / "rq9_optimal_age_summary.csv")
espn_match_df = pd.read_csv(RAW_DATA_PATH)

# Convert CSV text into numeric values so sorting, means, and charts work.
season_age_df["avg_age"] = pd.to_numeric(season_age_df["avg_age"], errors="coerce")
season_age_df["unique_players"] = pd.to_numeric(
    season_age_df["unique_players"],
    errors="coerce",
)

team_efficiency_df["avg_age"] = pd.to_numeric(
    team_efficiency_df["avg_age"],
    errors="coerce",
)
team_efficiency_df["goals_per_shot"] = pd.to_numeric(
    team_efficiency_df["goals_per_shot"],
    errors="coerce",
)
team_efficiency_df["matches"] = pd.to_numeric(
    team_efficiency_df["matches"],
    errors="coerce",
)
team_efficiency_df["total_goals"] = pd.to_numeric(
    team_efficiency_df["total_goals"],
    errors="coerce",
)
team_efficiency_df["total_shots"] = pd.to_numeric(
    team_efficiency_df["total_shots"],
    errors="coerce",
)

optimal_age_df["estimated_peak_age"] = pd.to_numeric(
    optimal_age_df["estimated_peak_age"],
    errors="coerce",
)
optimal_age_df["estimated_peak_goals_per_shot"] = pd.to_numeric(
    optimal_age_df["estimated_peak_goals_per_shot"],
    errors="coerce",
)

espn_match_df["age"] = pd.to_numeric(espn_match_df["age"], errors="coerce")
espn_match_df["player_goals"] = pd.to_numeric(
    espn_match_df["player_goals"],
    errors="coerce",
)
espn_match_df["player_shots"] = pd.to_numeric(
    espn_match_df["player_shots"],
    errors="coerce",
)

# Build the team selector choices once up front.
# The default selection is the top three teams by goals per shot.
RQ9_TEAM_OPTIONS = sorted(team_efficiency_df["team"].dropna().unique().tolist())
RQ9_DEFAULT_TEAMS = (
    team_efficiency_df.sort_values(
        "goals_per_shot",
        ascending=False,
        kind="stable",
    )
    .head(3)["team"]
    .dropna()
    .tolist()
)


def empty_figure(title):
    """Return an empty placeholder chart when there is no usable data."""

    fig = px.scatter(pd.DataFrame({"x": [], "y": []}), x="x", y="y", title=title)
    fig.update_layout(template="plotly_white")
    return fig


def sanitize_selected_teams(selected_teams, max_items=6):
    """Clean the team multi-select value.

    This keeps only valid teams, removes duplicates, and limits the amount of
    highlighted teams so the plots do not get too crowded.
    """

    if isinstance(selected_teams, str):
        selected_teams = [selected_teams]

    if not selected_teams:
        selected_teams = RQ9_DEFAULT_TEAMS

    valid_teams = []
    seen = set()
    for team in selected_teams:
        if team in RQ9_TEAM_OPTIONS and team not in seen:
            valid_teams.append(team)
            seen.add(team)

    if not valid_teams:
        valid_teams = list(RQ9_DEFAULT_TEAMS)

    return valid_teams[:max_items]


def build_league_age_text():
    """Build one short sentence with the league-wide age summary."""

    if season_age_df.empty:
        return ""

    row = season_age_df.iloc[0]
    if pd.isna(row["avg_age"]) or pd.isna(row["unique_players"]):
        return ""

    return (
        f"League average player age: {row['avg_age']:.2f} years across "
        f"{int(row['unique_players'])} players."
    )


def build_optimal_age_text():
    """Build the short explanation based on the quadratic model summary."""

    if optimal_age_df.empty:
        return ""

    row = optimal_age_df.iloc[0]
    text_parts = []

    if pd.notna(row["estimated_peak_age"]) and pd.notna(
        row["estimated_peak_goals_per_shot"]
    ):
        text_parts.append(
            "Estimated quadratic peak: "
            f"{row['estimated_peak_age']:.2f} years and "
            f"{row['estimated_peak_goals_per_shot']:.3f} goals per shot."
        )

    note = str(row["model_note"]).strip()
    if note and note.lower() != "nan":
        text_parts.append(note)

    return " ".join(text_parts)


def build_selected_team_note(selected_teams):
    """Build a readable sentence for the currently highlighted teams."""

    selected_teams = sanitize_selected_teams(selected_teams)
    selected_rows = team_efficiency_df.loc[
        team_efficiency_df["team"].isin(selected_teams)
    ].copy()

    if selected_rows.empty:
        return "No valid teams are selected."

    return (
        f"Selected teams: {', '.join(selected_teams)}. "
        f"They average {selected_rows['goals_per_shot'].mean():.3f} goals per shot "
        f"at an average squad age of {selected_rows['avg_age'].mean():.2f} years."
    )


def build_scatter_figure(selected_teams):
    """Build the team-age scatter plot.

    Selected teams are shown in red and labeled directly.
    Everyone else stays gray in the background.
    """

    filtered = team_efficiency_df.dropna(subset=["avg_age", "goals_per_shot"]).copy()
    if filtered.empty:
        return empty_figure("No team efficiency data available")

    selected_teams = sanitize_selected_teams(selected_teams)
    filtered["selected"] = filtered["team"].isin(selected_teams)

    fig = go.Figure()
    other_teams = filtered.loc[~filtered["selected"]].copy()
    selected_rows = filtered.loc[filtered["selected"]].copy()

    # Draw all non-selected teams first so they stay in the background.
    if not other_teams.empty:
        fig.add_trace(
            go.Scatter(
                x=other_teams["avg_age"],
                y=other_teams["goals_per_shot"],
                mode="markers",
                text=other_teams["team"],
                name="Other teams",
                marker=dict(color="#B0B0B0", size=10),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Average age: %{x:.2f}<br>"
                    "Goals per shot: %{y:.3f}<extra></extra>"
                ),
            )
        )

    # Draw the selected teams second so they stand out and get text labels.
    if not selected_rows.empty:
        fig.add_trace(
            go.Scatter(
                x=selected_rows["avg_age"],
                y=selected_rows["goals_per_shot"],
                mode="markers+text",
                text=selected_rows["team"],
                textposition="top center",
                name="Selected teams",
                marker=dict(color="#B22222", size=12),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Average age: %{x:.2f}<br>"
                    "Goals per shot: %{y:.3f}<extra></extra>"
                ),
            )
        )

    # Add a simple straight trend line across all teams.
    if len(filtered) >= 2:
        slope, intercept = np.polyfit(
            filtered["avg_age"],
            filtered["goals_per_shot"],
            1,
        )
        x_values = np.linspace(
            filtered["avg_age"].min(),
            filtered["avg_age"].max(),
            100,
        )
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=slope * x_values + intercept,
                mode="lines",
                line=dict(color="#444444", dash="dash"),
                name="Trend line",
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        template="plotly_white",
        title="Team Age vs Shot Efficiency",
        xaxis_title="Average Team Age",
        yaxis_title="Goals per Shot",
    )
    return fig


def build_ranking_figure(selected_teams, top_n):
    """Build the horizontal ranking chart for the top teams."""

    selected_teams = sanitize_selected_teams(selected_teams)
    filtered = team_efficiency_df.dropna(subset=["goals_per_shot"]).copy()
    filtered = filtered.sort_values(
        ["goals_per_shot", "team"],
        ascending=[False, True],
        kind="stable",
    ).head(int(top_n))
    filtered["selected"] = filtered["team"].isin(selected_teams)

    if filtered.empty:
        return empty_figure("No ranking data available")

    # Sort again before plotting so the weakest team is at the bottom and the
    # strongest team is at the top in the horizontal chart.
    fig = px.bar(
        filtered.sort_values(
            ["goals_per_shot", "team"],
            ascending=[True, True],
            kind="stable",
        ),
        x="goals_per_shot",
        y="team",
        orientation="h",
        color="selected",
        hover_data=["avg_age", "total_goals", "total_shots"],
        title=f"Top {int(top_n)} Teams by Goals per Shot",
        color_discrete_map={True: "#B22222", False: "#6E6E6E"},
    )
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        xaxis_title="Goals per Shot",
        yaxis_title="Team",
    )
    return fig


def get_dynamic_age_profile(min_total_shots):
    """Rebuild the player age profile from raw ESPN rows.

    This is the most dynamic part of the page:
    1. group raw player-match rows into age bands,
    2. compute goals, shots, and goals-per-shot per age band,
    3. mark which age bands pass the current minimum-shots threshold,
    4. return the best eligible age band.
    """

    age_frame = espn_match_df.loc[
        :, ["player_id", "age", "player_goals", "player_shots"]
    ].dropna(subset=["age"]).copy()

    if age_frame.empty:
        return pd.DataFrame(), None

    # Turn ages like 26.0 into integer age bands like 26.
    age_frame["age_int"] = age_frame["age"].astype(int)
    grouped = age_frame.groupby("age_int", as_index=False).agg(
        players=("player_id", "nunique"),
        total_goals=("player_goals", "sum"),
        total_shots=("player_shots", "sum"),
    )
    grouped = grouped.loc[grouped["total_shots"] > 0].copy()
    grouped["goals_per_shot"] = grouped["total_goals"] / grouped["total_shots"]
    grouped["eligible_threshold"] = grouped["total_shots"] >= int(min_total_shots)
    grouped = grouped.sort_values("age_int", kind="stable").reset_index(drop=True)

    eligible = grouped.loc[grouped["eligible_threshold"]].copy()
    eligible = eligible.sort_values(
        ["goals_per_shot", "total_shots", "age_int"],
        ascending=[False, False, True],
        kind="stable",
    )
    best_row = eligible.iloc[0] if not eligible.empty else None
    return grouped, best_row


def build_age_profile_figure(min_total_shots):
    """Build the dynamic player-age chart.

    Bars show shot volume.
    The line shows goals per shot.
    The star marks the best age band that passes the current threshold.
    """

    grouped, best_row = get_dynamic_age_profile(min_total_shots)
    if grouped.empty:
        return empty_figure("No player age profile could be computed"), best_row

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # Color age bands differently depending on whether they pass the current
    # minimum-shots threshold.
    bar_colors = [
        "rgba(178, 34, 34, 0.35)" if is_valid else "rgba(110, 110, 110, 0.35)"
        for is_valid in grouped["eligible_threshold"]
    ]
    fig.add_trace(
        go.Bar(
            x=grouped["age_int"],
            y=grouped["total_shots"],
            name="Total shots",
            marker=dict(color=bar_colors),
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=grouped["age_int"],
            y=grouped["goals_per_shot"],
            mode="lines+markers",
            name="Goals per shot",
            line=dict(color="#B22222", width=2),
            marker=dict(size=8),
        ),
        secondary_y=False,
    )

    # Add a star marker on the current best eligible age band.
    if best_row is not None:
        fig.add_trace(
            go.Scatter(
                x=[best_row["age_int"]],
                y=[best_row["goals_per_shot"]],
                mode="markers",
                name="Best eligible age",
                marker=dict(color="#7A0010", size=14, symbol="star"),
            ),
            secondary_y=False,
        )

    fig.update_layout(
        template="plotly_white",
        title="Player Age Profile by Goals per Shot and Volume",
    )
    fig.update_xaxes(title_text="Age Band")
    fig.update_yaxes(title_text="Goals per Shot", secondary_y=False)
    fig.update_yaxes(title_text="Total Shots", secondary_y=True)
    return fig, best_row


def build_age_profile_text(min_total_shots):
    """Build the short text below the dynamic age-profile chart."""

    _, best_row = get_dynamic_age_profile(min_total_shots)
    if best_row is None:
        return (
            f"No age band reaches the minimum threshold of {int(min_total_shots)} "
            "total shots."
        )

    return (
        f"With a minimum of {int(min_total_shots)} shots per age band, "
        f"age {int(best_row['age_int'])} leads with "
        f"{best_row['goals_per_shot']:.3f} goals per shot across "
        f"{int(best_row['players'])} players."
    )


league_age_text = build_league_age_text()
optimal_age_text = build_optimal_age_text()

# Initialize the app
app = Dash()

# The layout is intentionally simple:
# one chart selector, a few controls, one description, and one main graph.
app.layout = [
    html.Div(
        children=(
            "Research Question 9: Is there an ideal player age or average team "
            "age for strong shooting efficiency?"
        )
    ),
    html.Hr(),
    dcc.RadioItems(
        id="rq9_chart_selector",
        options=[
            {"label": "Age vs efficiency", "value": "scatter"},
            {"label": "Efficiency ranking", "value": "ranking"},
            {"label": "Player age profile", "value": "age_profile"},
        ],
        value="scatter",
        inline=True,
    ),
    html.Div(
        id="rq9_team_select_container",
        children=[
            html.Div("Highlight teams"),
            dcc.Dropdown(
                id="rq9_team_select",
                options=[
                    {"label": team, "value": team}
                    for team in RQ9_TEAM_OPTIONS
                ],
                value=RQ9_DEFAULT_TEAMS,
                multi=True,
            ),
        ],
        style={"marginTop": "16px"},
    ),
    html.Div(
        id="rq9_top_n_container",
        children=[
            html.Div("Ranking depth"),
            dcc.Slider(
                id="rq9_top_n",
                min=5,
                max=18,
                step=1,
                value=10,
                marks={5: "5", 10: "10", 15: "15", 18: "18"},
            ),
        ],
        style={"display": "none", "marginTop": "16px"},
    ),
    html.Div(
        id="rq9_min_shots_container",
        children=[
            html.Div("Minimum shots per age band"),
            dcc.Slider(
                id="rq9_min_shots",
                min=50,
                max=600,
                step=10,
                value=80,
                marks={50: "50", 80: "80", 200: "200", 400: "400", 600: "600"},
            ),
        ],
        style={"display": "none", "marginTop": "16px"},
    ),
    html.Div(
        id="plot_description",
        style={"marginTop": "20px", "fontWeight": "bold", "fontSize": "18px"},
    ),
    dcc.Graph(id="main_graph"),
]


@callback(
    Output("rq9_team_select_container", "style"),
    Output("rq9_top_n_container", "style"),
    Output("rq9_min_shots_container", "style"),
    Input("rq9_chart_selector", "value"),
)
def toggle_controls(chart_type):
    """Only show the controls needed for the current chart."""

    team_style = {"display": "block", "marginTop": "16px"}
    ranking_style = {"display": "block", "marginTop": "16px"}
    shots_style = {"display": "block", "marginTop": "16px"}

    if chart_type == "scatter":
        return team_style, {"display": "none"}, {"display": "none"}
    if chart_type == "ranking":
        return team_style, ranking_style, {"display": "none"}
    return {"display": "none"}, {"display": "none"}, shots_style


@callback(
    Output("main_graph", "figure"),
    Output("plot_description", "children"),
    Input("rq9_chart_selector", "value"),
    Input("rq9_team_select", "value"),
    Input("rq9_top_n", "value"),
    Input("rq9_min_shots", "value"),
)
def update_graph(chart_type, selected_teams, top_n, min_shots):
    """Build the current RQ9 chart and its explanation text."""

    if chart_type == "scatter":
        fig = build_scatter_figure(selected_teams)
        desc = (
            f"{build_selected_team_note(selected_teams)} "
            f"{league_age_text} {optimal_age_text}"
        ).strip()
    elif chart_type == "ranking":
        fig = build_ranking_figure(selected_teams, top_n)
        desc = (
            f"Top {int(top_n)} teams ranked by goals per shot. "
            "Selected teams are highlighted in red."
        )
    else:
        fig, _ = build_age_profile_figure(min_shots)
        desc = build_age_profile_text(min_shots)

    return fig, desc


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
