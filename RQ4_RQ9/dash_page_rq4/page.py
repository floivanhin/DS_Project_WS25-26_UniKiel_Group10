"""Build the RQ4 page and register its Dash callbacks.

Input: RQ4-derived CSV outputs and raw WhoScored match data.
Output: the RQ4 layout plus callback registration for its controls.
"""

import pathlib

import dash
import plotly.express as px

import Dash_Webapp.shared as shared
import RQ4_RQ9.dash_page_rq4.data as rq4_data


RQ4_MODE_LABELS = {
    "abs_delta": "largest home-away gaps",
    "home_specialists": "strongest home specialists",
    "away_specialists": "strongest away specialists",
}
RQ4_TEMPLATE_PATH = (
    pathlib.Path(__file__).resolve().parent / "page_template.html"
)
RQ4_DATA = rq4_data.load_rq4_data()
RQ4_RATINGS = RQ4_DATA.player_ratings.copy()
RQ4_DELTA = RQ4_DATA.player_delta.copy()
# Only players with enough home and away matches stay in the comparisons.
RQ4_ELIGIBLE_DELTA = RQ4_DELTA.loc[
    RQ4_DELTA["eligible_both_sides"]
].reset_index(drop=True)


def _sanitize_focus_player(player_name):
    """Pick a valid focus player for the RQ4 controls."""

    if player_name in RQ4_ELIGIBLE_DELTA["player"].tolist():
        return player_name

    return (
        RQ4_ELIGIBLE_DELTA.sort_values(
            "abs_avg_rating_delta", ascending=False
        )
        .iloc[0]["player"]
    )


def _get_league_metrics():
    """Calculate the main league-wide rating summary values."""

    leaderboard_rows = RQ4_RATINGS.loc[
        RQ4_RATINGS["eligible_for_leaderboard"]
    ].copy()
    home_rows = leaderboard_rows.loc[
        leaderboard_rows["home_away"] == "home"
    ]
    away_rows = leaderboard_rows.loc[
        leaderboard_rows["home_away"] == "away"
    ]
    top_home = home_rows.sort_values(
        "avg_overall_rating", ascending=False
    ).iloc[0]
    top_away = away_rows.sort_values(
        "avg_overall_rating", ascending=False
    ).iloc[0]

    return {
        "mean_home": home_rows["avg_overall_rating"].mean(),
        "mean_away": away_rows["avg_overall_rating"].mean(),
        "top_home": top_home,
        "top_away": top_away,
    }


def _get_leaderboard(view_mode, top_n):
    """Build the leaderboard table for the selected RQ4 view."""

    top_n = int(top_n)
    leaderboard = RQ4_ELIGIBLE_DELTA.copy()

    # Each view keeps the same base data but changes the filter and sort.
    if view_mode == "home_specialists":
        leaderboard = leaderboard.loc[
            leaderboard["avg_rating_delta_home_minus_away"] > 0
        ]
        leaderboard = leaderboard.sort_values(
            "avg_rating_delta_home_minus_away", ascending=False
        )
    elif view_mode == "away_specialists":
        leaderboard = leaderboard.loc[
            leaderboard["avg_rating_delta_home_minus_away"] < 0
        ]
        leaderboard = leaderboard.sort_values(
            "avg_rating_delta_home_minus_away"
        )
    else:
        leaderboard = leaderboard.sort_values(
            "abs_avg_rating_delta", ascending=False
        )

    return leaderboard.head(top_n).copy()


def _build_state(view_mode, top_n, focus_player):
    """Build all text and chart outputs for the current RQ4 state."""

    leaderboard = _get_leaderboard(view_mode, top_n)
    focus_player = _sanitize_focus_player(focus_player)
    focus_summary = RQ4_ELIGIBLE_DELTA.loc[
        RQ4_ELIGIBLE_DELTA["player"] == focus_player
    ].iloc[0]
    focus_matches = RQ4_DATA.whoscored_player_match_data.loc[
        RQ4_DATA.whoscored_player_match_data["player"] == focus_player
    ].copy()

    top_names = leaderboard["player"].head(3).tolist()
    answer_summary = (
        f"This view highlights the {RQ4_MODE_LABELS[view_mode]} in the "
        f"2024/25 Bundesliga data. The leading names right now are "
        f"{', '.join(top_names)}."
    )
    league_delta = RQ4_METRICS["mean_home"] - RQ4_METRICS["mean_away"]
    player_delta = focus_summary["avg_rating_delta_home_minus_away"]
    answer_detail = (
        f"Across all leaderboard-eligible players, the average home rating is "
        f"{shared._format_decimal(RQ4_METRICS['mean_home'], 3)} versus "
        f"{shared._format_decimal(RQ4_METRICS['mean_away'], 3)} away, a "
        f"league-wide delta of {shared._format_signed(league_delta, 3)}. "
        f"For {focus_player}, the summary delta is "
        f"{shared._format_signed(player_delta, 3)}."
    )

    # Reshape the summary table so Plotly can draw grouped home/away bars.
    compare_frame = leaderboard.loc[
        :,
        [
            "player",
            "home_avg_overall_rating",
            "away_avg_overall_rating",
        ],
    ].melt(
        id_vars="player",
        value_vars=[
            "home_avg_overall_rating",
            "away_avg_overall_rating",
        ],
        var_name="setting",
        value_name="avg_overall_rating",
    )
    compare_frame["setting"] = compare_frame["setting"].map(
        {
            "home_avg_overall_rating": "Home average",
            "away_avg_overall_rating": "Away average",
        }
    )

    compare_figure = px.bar(
        compare_frame,
        x="player",
        y="avg_overall_rating",
        color="setting",
        barmode="group",
        category_orders={"player": leaderboard["player"].tolist()},
        color_discrete_map={
            "Home average": shared.COLORS["red"],
            "Away average": shared.COLORS["neutral"],
        },
    )
    compare_figure.update_layout(title="Leaderboard comparison by player")
    compare_figure.update_xaxes(
        title="Player",
        tickangle=50,
        gridcolor="rgba(0, 0, 0, 0)",
    )
    compare_figure.update_yaxes(title="Average overall rating")
    compare_figure = shared._apply_base_layout(compare_figure, height=460)

    delta_figure = px.bar(
        leaderboard.sort_values("avg_rating_delta_home_minus_away"),
        x="avg_rating_delta_home_minus_away",
        y="player",
        orientation="h",
        color="avg_rating_delta_home_minus_away",
        color_continuous_scale=[
            shared.COLORS["neutral"],
            "#efc7ca",
            shared.COLORS["red"],
        ],
        labels={
            "avg_rating_delta_home_minus_away": "Home minus away",
            "player": "Player",
        },
    )
    delta_figure.update_layout(
        title="Home-away delta for the selected leaderboard",
        coloraxis_showscale=False,
    )
    delta_figure.update_xaxes(title="Rating delta")
    delta_figure.update_yaxes(title="Player")
    delta_figure = shared._apply_base_layout(delta_figure, height=520)

    if focus_matches.empty:
        focus_figure = shared._build_empty_figure(
            "No match-level ratings found.",
            height=560,
        )
    else:
        # Use readable labels in the match-level box plot.
        focus_matches = focus_matches.sort_values("home_away")
        focus_matches["home_away_label"] = focus_matches["home_away"].map(
            {"home": "Home", "away": "Away"}
        )
        focus_figure = px.box(
            focus_matches,
            x="home_away_label",
            y="overall_rating",
            color="home_away_label",
            points="all",
            category_orders={"home_away_label": ["Home", "Away"]},
            color_discrete_map={
                "Home": shared.COLORS["red"],
                "Away": shared.COLORS["neutral"],
            },
        )
        focus_figure.update_layout(
            title=f"Match-level ratings for {focus_player}",
            showlegend=False,
        )
        focus_figure.update_xaxes(title="Match setting")
        focus_figure.update_yaxes(title="WhoScored overall rating")
        focus_figure = shared._apply_base_layout(focus_figure, height=560)

    home_avg_text = shared._format_decimal(
        focus_summary["home_avg_overall_rating"],
        3,
    )
    away_avg_text = shared._format_decimal(
        focus_summary["away_avg_overall_rating"],
        3,
    )
    focus_note = (
        f"{focus_player} recorded {home_avg_text} at home across "
        f"{shared._format_count(focus_summary['home_matches'])} matches and "
        f"{away_avg_text} away across "
        f"{shared._format_count(focus_summary['away_matches'])} matches."
    )

    return {
        "answer_summary": answer_summary,
        "answer_detail": answer_detail,
        "compare_figure": compare_figure,
        "delta_figure": delta_figure,
        "focus_figure": focus_figure,
        "focus_note": focus_note,
    }


RQ4_METRICS = _get_league_metrics()
RQ4_INITIAL_STATE = _build_state(
    "abs_delta",
    10,
    _sanitize_focus_player(None),
)


def _build_top_player_metric():
    """Build the short top-player label shown in the metric cards."""

    top_home = RQ4_METRICS["top_home"]
    top_away = RQ4_METRICS["top_away"]
    if top_home["player"] == top_away["player"]:
        return (
            f"{top_home['player']} "
            f"{shared._format_decimal(top_home['avg_overall_rating'], 2)}/"
            f"{shared._format_decimal(top_away['avg_overall_rating'], 2)}"
        )

    return f"{top_home['player']} | {top_away['player']}"


def _build_delta_insights():
    """Create short text lines for the strongest positive and negative gaps."""

    top_positive = RQ4_ELIGIBLE_DELTA.loc[
        RQ4_ELIGIBLE_DELTA["avg_rating_delta_home_minus_away"] > 0
    ].sort_values("avg_rating_delta_home_minus_away", ascending=False)
    top_negative = RQ4_ELIGIBLE_DELTA.loc[
        RQ4_ELIGIBLE_DELTA["avg_rating_delta_home_minus_away"] < 0
    ].sort_values("avg_rating_delta_home_minus_away")
    positive_names = top_positive.head(3)["player"].tolist()
    negative_names = top_negative.head(3)["player"].tolist()

    return (
        "Strongest positive deltas: "
        f"{', '.join(positive_names)}.",
        "Strongest negative deltas: "
        f"{', '.join(negative_names)}.",
    )


def _build_metrics_cards():
    """Build the summary metric cards shown at the top of RQ4."""

    return [
        shared._build_metric_card(
            "Average home rating",
            shared._format_decimal(RQ4_METRICS["mean_home"], 3),
        ),
        shared._build_metric_card(
            "Average away rating",
            shared._format_decimal(RQ4_METRICS["mean_away"], 3),
        ),
        shared._build_metric_card(
            "Home minus away",
            shared._format_signed(
                RQ4_METRICS["mean_home"] - RQ4_METRICS["mean_away"],
                3,
            ),
        ),
        shared._build_metric_card(
            "Top player",
            _build_top_player_metric(),
        ),
    ]


def _build_view_mode_dropdown():
    """Build the dropdown for switching the RQ4 leaderboard view."""

    return dash.dcc.Dropdown(
        id="rq4-view-mode",
        options=[
            {
                "label": "Largest gaps",
                "value": "abs_delta",
            },
            {
                "label": "Home specialists",
                "value": "home_specialists",
            },
            {
                "label": "Away specialists",
                "value": "away_specialists",
            },
        ],
        value="abs_delta",
        clearable=False,
        className="control-input",
    )


def _build_focus_player_dropdown():
    """Build the dropdown for choosing the highlighted player."""

    return dash.dcc.Dropdown(
        id="rq4-player-select",
        options=[
            {
                "label": player,
                "value": player,
            }
            for player in sorted(RQ4_ELIGIBLE_DELTA["player"].tolist())
        ],
        value=_sanitize_focus_player(None),
        clearable=False,
        className="control-input",
    )


def _build_top_n_slider():
    """Build the slider that controls how many players are shown."""

    return dash.dcc.Slider(
        id="rq4-top-n",
        min=5,
        max=20,
        step=1,
        value=10,
        marks={
            5: "5",
            10: "10",
            15: "15",
            20: "20",
        },
    )


def _build_chart(component_id, figure):
    """Wrap a figure in a shared Dash graph component."""

    # component_id becomes the Dash id. Callbacks target this id to replace
    # the figure later, while the HTML template only decides where it appears.
    return dash.dcc.Graph(
        id=component_id,
        figure=figure,
        config=shared.GRAPH_CONFIG,
        className="chart-graph",
        style=shared._build_graph_style(figure),
    )


def _build_page_slots():
    """Build the template slot content used by the RQ4 page."""

    top_positive_text, top_negative_text = _build_delta_insights()
    eligible_label = (
        f"{shared._format_count(len(RQ4_ELIGIBLE_DELTA))} "
        "leaderboard-eligible on both sides"
    )

    return {
        "chip_summary_rows": dash.html.Span(
            (
                f"{shared._format_count(len(RQ4_RATINGS))} "
                "home/away summary rows"
            ),
            className="chip",
        ),
        "chip_player_comparisons": dash.html.Span(
            f"{shared._format_count(len(RQ4_DELTA))} player comparisons",
            className="chip",
        ),
        "chip_eligible_players": dash.html.Span(
            eligible_label,
            className="chip",
        ),
        "metrics": _build_metrics_cards(),
        "answer_summary": RQ4_INITIAL_STATE["answer_summary"],
        "answer_detail": RQ4_INITIAL_STATE["answer_detail"],
        "view_mode_dropdown": _build_view_mode_dropdown(),
        "player_select_dropdown": _build_focus_player_dropdown(),
        "top_n_slider": _build_top_n_slider(),
        "top_positive_text": top_positive_text,
        "top_negative_text": top_negative_text,
        # This key must match <slot name="compare_graph" /> in the HTML template.
        # shared._load_html_template() swaps that slot tag for this dcc.Graph.
        "compare_graph": _build_chart(
            "rq4-compare-chart",
            RQ4_INITIAL_STATE["compare_figure"],
        ),
        "focus_graph": _build_chart(
            "rq4-focus-chart",
            RQ4_INITIAL_STATE["focus_figure"],
        ),
        "focus_note": RQ4_INITIAL_STATE["focus_note"],
        "delta_graph": _build_chart(
            "rq4-delta-chart",
            RQ4_INITIAL_STATE["delta_figure"],
        ),
    }


def build_page():
    """Return the RQ4 layout for the Dash app."""

    # The HTML file provides the structure, and _build_page_slots() provides
    # the live Dash components that replace each <slot name="..."/> tag.
    return shared._load_html_template(
        RQ4_TEMPLATE_PATH,
        _build_page_slots(),
    )


def register_callbacks(app):
    """Register the RQ4 callbacks on the given Dash app."""

    @app.callback(
        dash.Output("rq4-answer-summary", "children"),
        dash.Output("rq4-answer-detail", "children"),
        dash.Output("rq4-compare-chart", "figure"),
        dash.Output("rq4-focus-chart", "figure"),
        dash.Output("rq4-delta-chart", "figure"),
        dash.Output("rq4-focus-note", "children"),
        dash.Input("rq4-view-mode", "value"),
        dash.Input("rq4-top-n", "value"),
        dash.Input("rq4-player-select", "value"),
    )
    def _update_dashboard(view_mode, top_n, focus_player):
        """Refresh the RQ4 text and charts when a control changes."""

        state = _build_state(view_mode, top_n, focus_player)
        return (
            state["answer_summary"],
            state["answer_detail"],
            state["compare_figure"],
            state["focus_figure"],
            state["delta_figure"],
            state["focus_note"],
        )
