"""Build the RQ9 page and register its Dash callbacks.

Input: RQ9-derived CSV outputs and raw ESPN player-match data.
Output: the RQ9 layout plus callback registration for its controls.
"""

import pathlib

import dash
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots

import Dash_Webapp.shared as shared
import RQ4_RQ9.dash_page_rq9.data as rq9_data


RQ9_DATA = rq9_data.load_rq9_data()
RQ9_TEMPLATE_PATH = (
    pathlib.Path(__file__).resolve().parent / "page_template.html"
)
RQ9_TEAM_EFFICIENCY = RQ9_DATA.team_age_efficiency.copy()
RQ9_TEAM_EFFICIENCY = RQ9_TEAM_EFFICIENCY.sort_values(
    "goals_per_shot", ascending=False
).reset_index(drop=True)
RQ9_TEAM_SUMMARY = RQ9_DATA.team_age_summary.copy()
RQ9_TEAM_SUMMARY = RQ9_TEAM_SUMMARY.sort_values(
    ["avg_age", "team"]
).reset_index(drop=True)
RQ9_MATCH_EFFICIENCY = RQ9_DATA.team_match_efficiency.copy()
RQ9_OPTIMAL_ROW = RQ9_DATA.optimal_age_summary.iloc[0]
RQ9_SEASON_LABEL = str(
    RQ9_DATA.season_age_summary.iloc[0]["season_label"]
)
RQ9_TEAM_OPTIONS = RQ9_TEAM_SUMMARY["team"].dropna().tolist()
# Start with the top three efficient teams highlighted.
RQ9_DEFAULT_TEAMS = (
    RQ9_TEAM_EFFICIENCY.head(3)["team"].dropna().tolist()
)
RQ9_MAX_COMPARE_TEAMS = 6


def _sanitize_selected_teams(selected_teams, default_teams, max_items=None):
    """Clean the selected team list and keep only valid team names."""

    if isinstance(selected_teams, str):
        selected_teams = [selected_teams]

    if not selected_teams:
        selected_teams = default_teams

    valid_teams = []
    seen = set()
    # Keep valid teams in the order the user selected them.
    for team in selected_teams:
        if team in RQ9_TEAM_OPTIONS and team not in seen:
            valid_teams.append(team)
            seen.add(team)

    if not valid_teams:
        valid_teams = list(default_teams)

    if max_items is not None:
        valid_teams = valid_teams[:max_items]

    return valid_teams


def _get_dynamic_age_profile(min_total_shots):
    """Rebuild the player age profile for the current shot threshold."""

    age_frame = RQ9_DATA.espn_player_match_data.loc[
        :, ["player_id", "age", "player_goals", "player_shots"]
    ].dropna(subset=["age"])
    age_frame = age_frame.copy()
    age_frame["age_int"] = age_frame["age"].astype(int)

    grouped = age_frame.groupby("age_int", as_index=False).agg(
        players=("player_id", "nunique"),
        total_goals=("player_goals", "sum"),
        total_shots=("player_shots", "sum"),
    )
    grouped = grouped.loc[grouped["total_shots"] > 0].copy()
    grouped["goals_per_shot"] = (
        grouped["total_goals"] / grouped["total_shots"]
    )
    grouped["eligible_threshold"] = grouped["total_shots"] >= int(
        min_total_shots
    )
    grouped = grouped.sort_values("age_int").reset_index(drop=True)

    eligible = grouped.loc[grouped["eligible_threshold"]].copy()
    eligible = eligible.sort_values(
        ["goals_per_shot", "total_shots", "age_int"],
        ascending=[False, False, True],
    )
    best_row = eligible.iloc[0] if not eligible.empty else None

    return grouped, best_row


def _build_state(selected_teams, top_n, min_total_shots):
    """Build all text and chart outputs for the current RQ9 state."""

    original_selected = selected_teams
    selected_teams = _sanitize_selected_teams(
        selected_teams,
        RQ9_DEFAULT_TEAMS,
        max_items=RQ9_MAX_COMPARE_TEAMS,
    )
    ranking_frame = RQ9_TEAM_EFFICIENCY.head(int(top_n)).copy()
    ranking_frame["selected"] = ranking_frame["team"].isin(selected_teams)

    scatter_frame = RQ9_TEAM_EFFICIENCY.copy()
    scatter_frame["selected"] = scatter_frame["team"].isin(selected_teams)
    trend_frame = shared._build_trend_line(
        scatter_frame,
        "avg_age",
        "goals_per_shot",
    )

    scatter_figure = go.Figure()
    # Split the teams so only the selected ones get labels and emphasis.
    unselected_frame = scatter_frame.loc[~scatter_frame["selected"]]
    selected_frame = scatter_frame.loc[scatter_frame["selected"]]

    if not unselected_frame.empty:
        scatter_figure.add_trace(
            go.Scatter(
                x=unselected_frame["avg_age"],
                y=unselected_frame["goals_per_shot"],
                mode="markers",
                name="Other teams",
                text=unselected_frame["team"],
                marker={
                    "size": 11,
                    "color": shared.COLORS["neutral_light"],
                    "line": {
                        "color": shared.COLORS["neutral"],
                        "width": 1,
                    },
                },
                hovertemplate=(
                    "<b>%{text}</b><br>Average age: %{x:.2f}<br>"
                    "Goals per shot: %{y:.3f}<extra></extra>"
                ),
            )
        )

    if not selected_frame.empty:
        scatter_figure.add_trace(
            go.Scatter(
                x=selected_frame["avg_age"],
                y=selected_frame["goals_per_shot"],
                mode="markers+text",
                name="Selected teams",
                text=selected_frame["team"],
                textposition="top center",
                marker={
                    "size": 13,
                    "color": shared.COLORS["red"],
                    "line": {
                        "color": shared.COLORS["red_dark"],
                        "width": 1.5,
                    },
                },
                hovertemplate=(
                    "<b>%{text}</b><br>Average age: %{x:.2f}<br>"
                    "Goals per shot: %{y:.3f}<extra></extra>"
                ),
            )
        )

    if not trend_frame.empty:
        scatter_figure.add_trace(
            go.Scatter(
                x=trend_frame["avg_age"],
                y=trend_frame["goals_per_shot"],
                mode="lines",
                name="Trend line",
                line={
                    "color": shared.COLORS["neutral"],
                    "dash": "dash",
                    "width": 2,
                },
                hoverinfo="skip",
            )
        )

    scatter_figure.update_layout(title="Team age vs. shot efficiency")
    scatter_figure.update_xaxes(title="Average team age")
    scatter_figure.update_yaxes(title="Goals per shot")
    scatter_figure = shared._apply_base_layout(scatter_figure, height=470)

    ranking_figure = px.bar(
        ranking_frame.sort_values("goals_per_shot"),
        x="goals_per_shot",
        y="team",
        orientation="h",
        color="selected",
        color_discrete_map={
            True: shared.COLORS["red"],
            False: shared.COLORS["neutral"],
        },
        labels={
            "goals_per_shot": "Goals per shot",
            "team": "Team",
            "selected": "Selection",
        },
    )
    ranking_figure.update_layout(
        title=f"Top {int(top_n)} teams by goals per shot",
        showlegend=False,
    )
    ranking_figure.update_xaxes(title="Goals per shot")
    ranking_figure.update_yaxes(title="Team")
    ranking_figure = shared._apply_base_layout(
        ranking_figure,
        height=max(420, (int(top_n) * 24) + 140),
    )

    match_frame = RQ9_MATCH_EFFICIENCY.loc[
        RQ9_MATCH_EFFICIENCY["team"].isin(selected_teams)
    ].copy()
    if match_frame.empty:
        match_figure = shared._build_empty_figure(
            "No team match data available."
        )
    else:
        match_figure = px.box(
            match_frame,
            x="goals_per_shot",
            y="team",
            color="team",
            points="all",
            category_orders={"team": selected_teams},
            color_discrete_sequence=[
                shared.COLORS["red"],
                shared.COLORS["red_dark"],
                "#ef7f87",
                shared.COLORS["neutral"],
                "#8a8a8a",
                "#c0c0c0",
            ],
        )
        match_figure.update_layout(
            title="Match-level efficiency for selected teams",
            showlegend=False,
        )
        match_figure.update_xaxes(title="Goals per shot")
        match_figure.update_yaxes(title="Team")
        match_figure = shared._apply_base_layout(match_figure, height=470)

    age_profile, best_row = _get_dynamic_age_profile(min_total_shots)
    if age_profile.empty:
        age_profile_figure = shared._build_empty_figure(
            "No player age profile could be computed.",
            height=600,
        )
        best_age_label = "n/a"
        band_efficiency_label = "n/a"
        best_age_note = "No age-band summary is available for this threshold."
    else:
        # Show shot volume and finishing efficiency together on two axes.
        age_profile_figure = plotly.subplots.make_subplots(
            specs=[[{"secondary_y": True}]]
        )
        bar_colors = [
            shared.COLORS["red_soft"] if is_valid else "#e5e5e5"
            for is_valid in age_profile["eligible_threshold"]
        ]
        age_profile_figure.add_trace(
            go.Bar(
                x=age_profile["age_int"],
                y=age_profile["total_shots"],
                name="Total shots",
                marker={
                    "color": bar_colors,
                    "line": {
                        "color": shared.COLORS["neutral_light"],
                        "width": 1,
                    },
                },
            ),
            secondary_y=True,
        )
        age_profile_figure.add_trace(
            go.Scatter(
                x=age_profile["age_int"],
                y=age_profile["goals_per_shot"],
                name="Goals per shot",
                mode="lines+markers",
                line={"color": shared.COLORS["red_dark"], "width": 3},
                marker={
                    "color": shared.COLORS["red"],
                    "size": 7,
                },
            ),
            secondary_y=False,
        )

        if best_row is not None:
            age_profile_figure.add_trace(
                go.Scatter(
                    x=[best_row["age_int"]],
                    y=[best_row["goals_per_shot"]],
                    name="Best eligible age",
                    mode="markers",
                    marker={
                        "color": shared.COLORS["red_dark"],
                        "size": 13,
                        "symbol": "star",
                    },
                ),
                secondary_y=False,
            )

        age_profile_figure.update_layout(
            title="Player age profile by goals per shot and volume",
        )
        age_profile_figure.update_xaxes(title="Age band")
        age_profile_figure.update_yaxes(
            title_text="Goals per shot",
            secondary_y=False,
        )
        age_profile_figure.update_yaxes(
            title_text="Total shots",
            secondary_y=True,
            gridcolor="rgba(0, 0, 0, 0)",
        )
        age_profile_figure = shared._apply_base_layout(
            age_profile_figure,
            height=600,
        )

        if best_row is None:
            best_age_label = "n/a"
            band_efficiency_label = "n/a"
            best_age_note = (
                f"No age band reaches the minimum threshold of "
                f"{int(min_total_shots)} total shots."
            )
        else:
            best_age_label = f"{int(best_row['age_int'])} years"
            band_efficiency_label = (
                f"{shared._format_decimal(best_row['goals_per_shot'], 3)} "
                f"({shared._format_count(best_row['total_goals'])}/"
                f"{shared._format_count(best_row['total_shots'])})"
            )
            best_age_note = (
                f"With a minimum of {int(min_total_shots)} shots per "
                f"age band, age {int(best_row['age_int'])} leads with "
                f"{shared._format_decimal(best_row['goals_per_shot'], 3)} "
                f"goals per shot across "
                f"{shared._format_count(best_row['players'])} players."
            )

    selected_summary = RQ9_TEAM_EFFICIENCY.loc[
        RQ9_TEAM_EFFICIENCY["team"].isin(selected_teams)
    ].copy()
    selected_mean_efficiency = shared._format_decimal(
        selected_summary["goals_per_shot"].mean(),
        3,
    )
    selected_mean_age = shared._format_decimal(
        selected_summary["avg_age"].mean(),
        2,
    )
    team_note = (
        f"Selected teams: {', '.join(selected_teams)}. Together they average "
        f"{selected_mean_efficiency} goals per shot at a mean squad age of "
        f"{selected_mean_age} years."
    )
    if original_selected and len(selected_teams) < len(original_selected):
        # The selector can hold more teams than the comparison plot can show.
        team_note += (
            f" Only the first {RQ9_MAX_COMPARE_TEAMS} selected teams are "
            f"shown in the match comparison for readability."
        )

    return {
        "scatter_figure": scatter_figure,
        "ranking_figure": ranking_figure,
        "match_figure": match_figure,
        "age_profile_figure": age_profile_figure,
        "best_age_label": best_age_label,
        "band_efficiency_label": band_efficiency_label,
        "best_age_note": best_age_note,
        "team_note": team_note,
    }


RQ9_INITIAL_STATE = _build_state(RQ9_DEFAULT_TEAMS, 10, 80)


def _build_ranking_depth_control():
    """Build the slider that controls the ranking chart depth."""

    return dash.html.Div(
        className="control-group",
        children=[
            dash.html.Label(
                "Ranking depth",
                className="control-label",
            ),
            dash.dcc.Slider(
                id="rq9-top-n",
                min=5,
                max=18,
                step=1,
                value=10,
                marks={
                    5: "5",
                    10: "10",
                    15: "15",
                    18: "18",
                },
            ),
        ],
    )


def _build_chart(component_id, figure):
    """Wrap a figure in a shared Dash graph component."""

    return dash.dcc.Graph(
        id=component_id,
        figure=figure,
        config=shared.GRAPH_CONFIG,
        className="chart-graph",
        style=shared._build_graph_style(figure),
    )


def _build_team_select_dropdown():
    """Build the multi-select dropdown for team highlighting."""

    return dash.dcc.Dropdown(
        id="rq9-team-select",
        options=[
            {"label": team, "value": team}
            for team in RQ9_TEAM_OPTIONS
        ],
        value=RQ9_DEFAULT_TEAMS,
        multi=True,
        className="control-input",
    )


def _build_min_shots_control():
    """Build the slider control for the age-band shot threshold."""

    return dash.html.Div(
        className="control-group",
        children=[
            dash.html.Label(
                "Minimum shots per age band",
                className="control-label",
            ),
            dash.dcc.Slider(
                id="rq9-min-shots",
                min=50,
                max=600,
                step=10,
                value=80,
                marks={
                    50: "50",
                    80: "80",
                    200: "200",
                    400: "400",
                    600: "600",
                },
            ),
        ],
    )


def _build_team_age_figure():
    """Build the bar chart for average age per team."""

    figure = px.bar(
        RQ9_TEAM_SUMMARY,
        x="team",
        y="avg_age",
        text="avg_age",
    )
    figure.update_traces(
        marker_color=shared.COLORS["red"],
        marker_line_color=shared.COLORS["red_dark"],
        marker_line_width=1.2,
        opacity=0.8,
        texttemplate="%{text:.2f}",
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>Average age: %{y:.2f}<br>"
            "Players: %{customdata[0]}<extra></extra>"
        ),
        customdata=RQ9_TEAM_SUMMARY[["player_count"]].to_numpy(),
    )
    figure.update_layout(
        title="Average age per team",
        showlegend=False,
    )
    figure.update_xaxes(
        tickangle=50,
        title="Team",
        gridcolor="rgba(0, 0, 0, 0)",
    )
    figure.update_yaxes(title="Years")
    return shared._apply_base_layout(figure, height=480)


def _build_page_slots():
    """Build the template slot content used by the RQ9 page."""

    top_teams = RQ9_TEAM_EFFICIENCY.head(3)["team"].tolist()
    low_teams = (
        RQ9_TEAM_EFFICIENCY.sort_values("goals_per_shot")
        .head(3)["team"]
        .tolist()
    )
    youngest_team = RQ9_TEAM_SUMMARY.iloc[0]
    oldest_team = RQ9_TEAM_SUMMARY.iloc[-1]
    team_age_figure = _build_team_age_figure()

    return {
        "chip_team_count": dash.html.Span(
            f"{shared._format_count(len(RQ9_TEAM_OPTIONS))} teams",
            className="chip",
        ),
        "chip_match_rows": dash.html.Span(
            (
                f"{shared._format_count(len(RQ9_MATCH_EFFICIENCY))} "
                "team-match rows"
            ),
            className="chip",
        ),
        "chip_pearson": dash.html.Span(
            (
                "Pearson r = "
                f"{shared._format_decimal(
                    RQ9_OPTIMAL_ROW['pearson_r_age_efficiency'],
                    3,
                )}"
            ),
            className="chip",
        ),
        "chip_season": dash.html.Span(
            f"Season: {RQ9_SEASON_LABEL}",
            className="chip",
        ),
        "metrics": [
            shared._build_metric_card(
                "Pearson r",
                shared._format_decimal(
                    RQ9_OPTIMAL_ROW["pearson_r_age_efficiency"],
                    3,
                ),
            ),
            shared._build_metric_card(
                "Observed team age range",
                (
                    f"{shared._format_decimal(
                        RQ9_TEAM_EFFICIENCY['avg_age'].min(),
                        2,
                    )}-"
                    f"{shared._format_decimal(
                        RQ9_TEAM_EFFICIENCY['avg_age'].max(),
                        2,
                    )}"
                ),
            ),
            shared._build_metric_card(
                "Best age band",
                RQ9_INITIAL_STATE["best_age_label"],
                value_id="rq9-metric-best-age",
            ),
            shared._build_metric_card(
                "Band efficiency",
                RQ9_INITIAL_STATE["band_efficiency_label"],
                value_id="rq9-metric-band-efficiency",
            ),
            shared._build_metric_card(
                "Estimated peak age",
                (
                    f"{shared._format_decimal(
                        RQ9_OPTIMAL_ROW['estimated_peak_age'],
                        2,
                    )} years"
                ),
            ),
            shared._build_metric_card(
                "Estimated peak efficiency",
                shared._format_decimal(
                    RQ9_OPTIMAL_ROW["estimated_peak_goals_per_shot"],
                    3,
                ),
            ),
        ],
        "top_teams_text": (
            f"Top efficiency teams: {', '.join(top_teams)}."
        ),
        "low_teams_text": (
            f"Lowest efficiency teams: {', '.join(low_teams)}."
        ),
        "team_select_dropdown": _build_team_select_dropdown(),
        "team_note": RQ9_INITIAL_STATE["team_note"],
        "scatter_graph": _build_chart(
            "rq9-scatter-chart",
            RQ9_INITIAL_STATE["scatter_figure"],
        ),
        "ranking_depth_control": _build_ranking_depth_control(),
        "ranking_graph": _build_chart(
            "rq9-ranking-chart",
            RQ9_INITIAL_STATE["ranking_figure"],
        ),
        "match_graph": _build_chart(
            "rq9-match-chart",
            RQ9_INITIAL_STATE["match_figure"],
        ),
        "summary_chart_note": (
            "This chart was previously on the summary page and now sits in "
            "RQ9 where the team age context directly supports the age vs. "
            "efficiency discussion."
        ),
        "current_extremes_text": (
            f"Current extremes: {youngest_team['team']} "
            f"({shared._format_decimal(youngest_team['avg_age'], 2)}) and "
            f"{oldest_team['team']} "
            f"({shared._format_decimal(oldest_team['avg_age'], 2)})."
        ),
        "team_age_graph": _build_chart(
            "rq9-team-age-chart",
            team_age_figure,
        ),
        "min_shots_control": _build_min_shots_control(),
        "age_profile_graph": _build_chart(
            "rq9-age-profile-chart",
            RQ9_INITIAL_STATE["age_profile_figure"],
        ),
        "best_age_note": RQ9_INITIAL_STATE["best_age_note"],
    }


def build_page():
    """Return the RQ9 layout for the Dash app."""

    return shared._load_html_template(
        RQ9_TEMPLATE_PATH,
        _build_page_slots(),
    )


def register_callbacks(app):
    """Register the RQ9 callbacks on the given Dash app."""

    @app.callback(
        dash.Output("rq9-scatter-chart", "figure"),
        dash.Output("rq9-scatter-chart", "style"),
        dash.Output("rq9-ranking-chart", "figure"),
        dash.Output("rq9-ranking-chart", "style"),
        dash.Output("rq9-match-chart", "figure"),
        dash.Output("rq9-match-chart", "style"),
        dash.Output("rq9-age-profile-chart", "figure"),
        dash.Output("rq9-age-profile-chart", "style"),
        dash.Output("rq9-metric-best-age", "children"),
        dash.Output("rq9-metric-band-efficiency", "children"),
        dash.Output("rq9-best-age-note", "children"),
        dash.Output("rq9-team-note", "children"),
        dash.Input("rq9-team-select", "value"),
        dash.Input("rq9-top-n", "value"),
        dash.Input("rq9-min-shots", "value"),
    )
    def _update_dashboard(selected_teams, top_n, min_total_shots):
        """Refresh the RQ9 text and charts when a control changes."""

        state = _build_state(selected_teams, top_n, min_total_shots)
        return (
            state["scatter_figure"],
            shared._build_graph_style(state["scatter_figure"]),
            state["ranking_figure"],
            shared._build_graph_style(state["ranking_figure"]),
            state["match_figure"],
            shared._build_graph_style(state["match_figure"]),
            state["age_profile_figure"],
            shared._build_graph_style(state["age_profile_figure"]),
            state["best_age_label"],
            state["band_efficiency_label"],
            state["best_age_note"],
            state["team_note"],
        )
