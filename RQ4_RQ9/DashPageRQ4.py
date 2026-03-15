# Import packages
from pathlib import Path

from dash import Dash, Input, Output, callback, dcc, html
import pandas as pd
import plotly.express as px

# These paths make the file work no matter from where the script is started.
# `BASE_DIR` is the folder that contains this Python file.
BASE_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = BASE_DIR / "analysis_output" / "rq4"
RAW_DATA_PATH = (
    BASE_DIR
    / "data"
    / "downloaded_outputs_to_analyse"
    / "whoscored_player_match_data_for_rq4.csv"
)

# Load the already prepared analysis tables plus the raw match-level file.
# The analysis tables are used for the summary charts.
# The raw match file is only needed for the player focus box plot.
ratings_df = pd.read_csv(ANALYSIS_DIR / "rq4_home_away_player_ratings.csv")
delta_df = pd.read_csv(ANALYSIS_DIR / "rq4_player_home_away_delta.csv")
match_df = pd.read_csv(RAW_DATA_PATH)

# Convert text columns from the CSV into real numbers/booleans.
# This avoids bad sorting and makes the charts behave correctly.
ratings_df["avg_overall_rating"] = pd.to_numeric(
    ratings_df["avg_overall_rating"],
    errors="coerce",
)
ratings_df["matches"] = pd.to_numeric(ratings_df["matches"], errors="coerce")
ratings_df["eligible_for_leaderboard"] = (
    ratings_df["eligible_for_leaderboard"].astype(str).str.lower() == "true"
)

delta_df["home_avg_overall_rating"] = pd.to_numeric(
    delta_df["home_avg_overall_rating"],
    errors="coerce",
)
delta_df["away_avg_overall_rating"] = pd.to_numeric(
    delta_df["away_avg_overall_rating"],
    errors="coerce",
)
delta_df["avg_rating_delta_home_minus_away"] = pd.to_numeric(
    delta_df["avg_rating_delta_home_minus_away"],
    errors="coerce",
)
delta_df["abs_avg_rating_delta"] = pd.to_numeric(
    delta_df["abs_avg_rating_delta"],
    errors="coerce",
)
delta_df["home_matches"] = pd.to_numeric(
    delta_df["home_matches"],
    errors="coerce",
)
delta_df["away_matches"] = pd.to_numeric(
    delta_df["away_matches"],
    errors="coerce",
)
delta_df["eligible_both_sides"] = (
    delta_df["eligible_both_sides"].astype(str).str.lower() == "true"
)

match_df["overall_rating"] = pd.to_numeric(
    match_df["overall_rating"],
    errors="coerce",
)

# Human-readable labels for the leaderboard mode control.
RQ4_MODE_LABELS = {
    "abs_delta": "largest home-away gaps",
    "home_specialists": "strongest home specialists",
    "away_specialists": "strongest away specialists",
}

# Keep a cleaned "eligible only" table because many views should only use
# players that have enough home and away matches to be compared fairly.
RQ4_ELIGIBLE_DELTA = delta_df.loc[delta_df["eligible_both_sides"]].copy()
RQ4_PLAYER_OPTIONS = sorted(RQ4_ELIGIBLE_DELTA["player"].dropna().unique().tolist())

# Precompute the league-wide home/away means once so callbacks stay simple.
leaderboard_rows = ratings_df.loc[ratings_df["eligible_for_leaderboard"]].copy()
home_rows = leaderboard_rows.loc[leaderboard_rows["home_away"] == "home"].copy()
away_rows = leaderboard_rows.loc[leaderboard_rows["home_away"] == "away"].copy()
MEAN_HOME = home_rows["avg_overall_rating"].mean()
MEAN_AWAY = away_rows["avg_overall_rating"].mean()


def empty_figure(title):
    """Return an empty placeholder chart when there is no usable data."""

    fig = px.scatter(pd.DataFrame({"x": [], "y": []}), x="x", y="y", title=title)
    fig.update_layout(template="plotly_white")
    return fig


def sanitize_focus_player(player_name):
    """Return a valid player name for the focus-player dropdown.

    If the incoming value is missing or invalid, fall back to the player with
    the biggest absolute home-away gap.
    """

    if player_name in RQ4_PLAYER_OPTIONS:
        return player_name

    if not RQ4_PLAYER_OPTIONS:
        return None

    default_row = RQ4_ELIGIBLE_DELTA.sort_values(
        "abs_avg_rating_delta",
        ascending=False,
        kind="stable",
    ).iloc[0]
    return str(default_row["player"])


def get_leaderboard(view_mode, top_n):
    """Build the player subset for the current leaderboard mode.

    `abs_delta` keeps the biggest differences overall.
    `home_specialists` keeps players who are clearly better at home.
    `away_specialists` keeps players who are clearly better away.
    """

    leaderboard = RQ4_ELIGIBLE_DELTA.copy()

    if view_mode == "home_specialists":
        leaderboard = leaderboard.loc[
            leaderboard["avg_rating_delta_home_minus_away"] > 0
        ]
        leaderboard = leaderboard.sort_values(
            ["avg_rating_delta_home_minus_away", "player"],
            ascending=[False, True],
            kind="stable",
        )
    elif view_mode == "away_specialists":
        leaderboard = leaderboard.loc[
            leaderboard["avg_rating_delta_home_minus_away"] < 0
        ]
        leaderboard = leaderboard.sort_values(
            ["avg_rating_delta_home_minus_away", "player"],
            ascending=[True, True],
            kind="stable",
        )
    else:
        leaderboard = leaderboard.sort_values(
            ["abs_avg_rating_delta", "player"],
            ascending=[False, True],
            kind="stable",
        )

    return leaderboard.head(int(top_n)).copy()


def build_compare_figure(view_mode, top_n):
    """Build the grouped bar chart for home vs away averages.

    This answers: for the selected leaderboard, how do the home and away
    averages compare side by side for each player?
    """

    leaderboard = get_leaderboard(view_mode, top_n)
    if leaderboard.empty:
        return empty_figure("No comparison data available")

    # Convert one row per player into two rows per player so Plotly can draw
    # a grouped bar chart: one bar for home and one for away.
    compare_df = pd.concat(
        [
            leaderboard[["player", "home_avg_overall_rating"]]
            .rename(columns={"home_avg_overall_rating": "avg_overall_rating"})
            .assign(setting="Home"),
            leaderboard[["player", "away_avg_overall_rating"]]
            .rename(columns={"away_avg_overall_rating": "avg_overall_rating"})
            .assign(setting="Away"),
        ],
        ignore_index=True,
    )

    fig = px.bar(
        compare_df,
        x="player",
        y="avg_overall_rating",
        color="setting",
        barmode="group",
        category_orders={"player": leaderboard["player"].tolist()},
        title="Leaderboard Comparison by Player",
        color_discrete_map={"Home": "#2E8B57", "Away": "#1F77B4"},
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Player",
        yaxis_title="Average Overall Rating",
    )
    fig.update_xaxes(tickangle=50)
    return fig


def build_delta_figure(view_mode, top_n):
    """Build the horizontal bar chart for home-away rating differences."""

    leaderboard = get_leaderboard(view_mode, top_n)
    if leaderboard.empty:
        return empty_figure("No delta data available")

    # Sort from most negative to most positive so the horizontal chart is easy
    # to read from bottom to top.
    chart_df = leaderboard.sort_values(
        "avg_rating_delta_home_minus_away",
        ascending=True,
        kind="stable",
    ).copy()
    # Turn the numeric sign into a readable label so the colors make sense.
    chart_df["direction"] = chart_df["avg_rating_delta_home_minus_away"].apply(
        lambda value: "Better Away" if value < 0 else "Better Home"
    )

    fig = px.bar(
        chart_df,
        x="avg_rating_delta_home_minus_away",
        y="player",
        orientation="h",
        color="direction",
        hover_data=["home_matches", "away_matches"],
        title="Home-Away Delta for the Selected Leaderboard",
        color_discrete_map={
            "Better Home": "#2E8B57",
            "Better Away": "#B22222",
        },
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Average Rating Delta (Home - Away)",
        yaxis_title="Player",
    )
    return fig


def build_focus_figure(player_name):
    """Build the match-level box plot for one selected player.

    This uses raw match rows instead of the aggregated summary tables because
    we want to show the spread of individual match ratings.
    """

    player_name = sanitize_focus_player(player_name)
    if player_name is None:
        return empty_figure("No focus player available")

    focus_matches = match_df.loc[match_df["player"] == player_name].copy()
    focus_matches = focus_matches.dropna(subset=["overall_rating"])
    if focus_matches.empty:
        return empty_figure("No match-level ratings found")

    # Replace the short machine values with labels that look nicer in the UI.
    focus_matches["home_away_label"] = focus_matches["home_away"].map(
        {"home": "Home", "away": "Away"}
    )
    fig = px.box(
        focus_matches,
        x="home_away_label",
        y="overall_rating",
        color="home_away_label",
        points="all",
        category_orders={"home_away_label": ["Home", "Away"]},
        title=f"Match-Level Ratings for {player_name}",
        color_discrete_map={"Home": "#2E8B57", "Away": "#1F77B4"},
    )
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        xaxis_title="Match Setting",
        yaxis_title="WhoScored Overall Rating",
    )
    return fig


def build_league_summary_text():
    """Build one short sentence with the overall league home/away means."""

    if pd.isna(MEAN_HOME) or pd.isna(MEAN_AWAY):
        return ""

    return (
        f"League-wide mean home rating: {MEAN_HOME:.3f}; "
        f"away rating: {MEAN_AWAY:.3f}; "
        f"delta: {MEAN_HOME - MEAN_AWAY:+.3f}."
    )


def build_focus_text(player_name):
    """Build the short text that explains the selected focus player."""

    player_name = sanitize_focus_player(player_name)
    if player_name is None:
        return "No focus player available."

    summary = RQ4_ELIGIBLE_DELTA.loc[RQ4_ELIGIBLE_DELTA["player"] == player_name]
    if summary.empty:
        return f"No eligible home-away summary is available for {player_name}."

    row = summary.iloc[0]
    return (
        f"{player_name} recorded {row['home_avg_overall_rating']:.3f} at home "
        f"across {int(row['home_matches'])} matches and "
        f"{row['away_avg_overall_rating']:.3f} away across "
        f"{int(row['away_matches'])} matches."
    )


# Initialize the app
app = Dash()

# The layout is the visible page structure: title, controls, short text,
# and one graph that changes when the controls change.
app.layout = [
    html.Div(
        children=(
            "Research Question 4: How does playing at home compared to away "
            "affect player performance ratings?"
        )
    ),
    html.Hr(),
    dcc.RadioItems(
        id="rq4_chart_selector",
        options=[
            {"label": "Leaderboard comparison", "value": "compare"},
            {"label": "Delta view", "value": "delta"},
            {"label": "Focus player", "value": "focus"},
        ],
        value="compare",
        inline=True,
    ),
    html.Div(
        id="rq4_leaderboard_controls",
        children=[
            html.Div("Leaderboard mode"),
            dcc.Dropdown(
                id="rq4_view_mode",
                options=[
                    {"label": "Largest gaps", "value": "abs_delta"},
                    {"label": "Home specialists", "value": "home_specialists"},
                    {"label": "Away specialists", "value": "away_specialists"},
                ],
                value="abs_delta",
                clearable=False,
            ),
            html.Div("Top players", style={"marginTop": "16px"}),
            dcc.Slider(
                id="rq4_top_n",
                min=5,
                max=20,
                step=1,
                value=10,
                marks={5: "5", 10: "10", 15: "15", 20: "20"},
            ),
        ],
        style={"marginTop": "16px"},
    ),
    html.Div(
        id="rq4_focus_player_container",
        children=[
            html.Div("Focus player"),
            dcc.Dropdown(
                id="rq4_focus_player",
                options=[
                    {"label": player, "value": player}
                    for player in RQ4_PLAYER_OPTIONS
                ],
                value=sanitize_focus_player(None),
                clearable=False,
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
    Output("rq4_leaderboard_controls", "style"),
    Output("rq4_focus_player_container", "style"),
    Input("rq4_chart_selector", "value"),
)
def toggle_controls(chart_type):
    """Show only the controls that matter for the current chart.

    Compare/delta views need leaderboard controls.
    Focus view only needs the player selector.
    """

    leaderboard_style = {"display": "block", "marginTop": "16px"}
    focus_style = {"display": "block", "marginTop": "16px"}

    if chart_type == "focus":
        return {"display": "none"}, focus_style

    return leaderboard_style, {"display": "none"}


@callback(
    Output("main_graph", "figure"),
    Output("plot_description", "children"),
    Input("rq4_chart_selector", "value"),
    Input("rq4_view_mode", "value"),
    Input("rq4_top_n", "value"),
    Input("rq4_focus_player", "value"),
)
def update_graph(chart_type, view_mode, top_n, focus_player):
    """Build the current figure and the short explanation below the controls."""

    league_text = build_league_summary_text()

    if chart_type == "compare":
        fig = build_compare_figure(view_mode, top_n)
        desc = (
            f"This view highlights the {RQ4_MODE_LABELS[view_mode]}. "
            f"{league_text}"
        )
    elif chart_type == "delta":
        fig = build_delta_figure(view_mode, top_n)
        desc = (
            "Positive values mean a player performed better at home, "
            "negative values mean better away. "
            f"{league_text}"
        )
    else:
        fig = build_focus_figure(focus_player)
        desc = build_focus_text(focus_player)

    return fig, desc


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
