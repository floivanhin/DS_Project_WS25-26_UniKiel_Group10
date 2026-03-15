"""Build the RQ3 page and register its Dash callbacks.

Input: local RQ3 shot-transition CSV data.
Output: the RQ3 layout plus callback registration for its controls.
"""

import pathlib

import dash
import pandas as pd
import plotly.express as px

import Dash_Webapp.shared as shared


RQ3_DATA_PATH = pathlib.Path(__file__).resolve().parent.parent / "RQ3.csv"
RQ3_TEMPLATE_PATH = (
    pathlib.Path(__file__).resolve().parent / "page_template.html"
)
INTERVAL_BINS = [0, 10, 15, 20, 25, 30, 35, 40, 45, 50, float("inf")]
INTERVAL_LABELS = [
    "0-10s",
    "10-15s",
    "15-20s",
    "20-25s",
    "25-30s",
    "30-35s",
    "35-40s",
    "40-45s",
    "45-50s",
    "50s+",
]


def _normalize_bool(series):
    """Turn mixed true/false values into clean boolean values."""

    return (
        series.fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
    )


def _load_rq3_data():
    """Load and clean the RQ3 CSV file."""

    if not RQ3_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Required RQ3 dataset is missing: {RQ3_DATA_PATH}"
        )

    frame = pd.read_csv(RQ3_DATA_PATH)
    required_columns = {"is_goal", "time_delta"}
    if not required_columns.issubset(frame.columns):
        raise ValueError(
            "RQ3 CSV is missing required columns: "
            f"{sorted(required_columns - set(frame.columns))}"
        )

    frame = frame.loc[:, ["is_goal", "time_delta"]].copy()
    frame["is_goal"] = _normalize_bool(frame["is_goal"])
    frame["time_delta"] = pd.to_numeric(
        frame["time_delta"],
        errors="coerce",
    )
    frame = frame.dropna(subset=["time_delta"])
    frame["interval"] = pd.cut(
        frame["time_delta"],
        bins=INTERVAL_BINS,
        labels=INTERVAL_LABELS,
        include_lowest=True,
    )
    frame = frame.dropna(subset=["interval"])

    return frame


def _build_interval_summary(frame):
    """Build one summary row per transition-time interval."""

    rows = []
    for label in INTERVAL_LABELS:
        subset = frame.loc[frame["interval"] == label]
        goal_count = int(subset.loc[subset["is_goal"]].shape[0])
        no_goal_count = int(subset.loc[~subset["is_goal"]].shape[0])
        total_shots = goal_count + no_goal_count
        if total_shots == 0:
            conversion_rate = 0.0
        else:
            conversion_rate = (goal_count / total_shots) * 100

        rows.append(
            {
                "interval": label,
                "goal_count": goal_count,
                "no_goal_count": no_goal_count,
                "total_shots": total_shots,
                "conversion_rate": conversion_rate,
            }
        )

    return pd.DataFrame(rows)


def _build_bar_figure(summary):
    """Build the stacked shot-result count bar chart."""

    chart_data = pd.concat(
        [
            pd.DataFrame(
                {
                    "interval": summary["interval"],
                    "count": summary["no_goal_count"],
                    "outcome": "No Goal",
                }
            ),
            pd.DataFrame(
                {
                    "interval": summary["interval"],
                    "count": summary["goal_count"],
                    "outcome": "Goal",
                }
            ),
        ],
        ignore_index=True,
    )

    figure = px.bar(
        chart_data,
        x="interval",
        y="count",
        color="outcome",
        color_discrete_map={
            "No Goal": "#d20515",
            "Goal": "#27ae60",
        },
        title="Shots and goals by transition-time interval",
    )
    figure.update_layout(
        barmode="stack",
        legend_title_text="Result",
    )
    figure.update_xaxes(
        title="Seconds after possession win",
        categoryorder="array",
        categoryarray=INTERVAL_LABELS,
        gridcolor="rgba(0, 0, 0, 0)",
    )
    figure.update_yaxes(title="Count")
    return shared._apply_base_layout(figure, height=520)


def _build_line_figure(summary):
    """Build the conversion-rate line chart."""

    figure = px.line(
        summary,
        x="interval",
        y="conversion_rate",
        title="Goal conversion rate per transition-time interval",
        markers=True,
    )
    figure.update_traces(
        line_color="#27ae60",
        line_width=3,
        marker={"size": 8},
    )
    figure.update_xaxes(
        title="Seconds after possession win",
        categoryorder="array",
        categoryarray=INTERVAL_LABELS,
    )
    figure.update_yaxes(title="Conversion rate (%)")
    return shared._apply_base_layout(figure, height=520)


def _get_plot_description(chart_mode):
    """Return the explanatory text for the selected chart mode."""

    if chart_mode == "line":
        return (
            "Percentage of shots that turned into goals, grouped by the "
            "time between winning possession in the own half and shooting."
        )

    return (
        "Counts of all shots split into goals and non-goals, grouped by the "
        "time between winning possession in the own half and shooting."
    )


def _build_metrics_cards():
    """Build summary metric cards for the RQ3 page."""

    total_shots = int(RQ3_INTERVAL_SUMMARY["total_shots"].sum())
    total_goals = int(RQ3_INTERVAL_SUMMARY["goal_count"].sum())
    if total_shots == 0:
        overall_conversion = float("nan")
    else:
        overall_conversion = (total_goals / total_shots) * 100

    best_interval_row = RQ3_INTERVAL_SUMMARY.sort_values(
        ["conversion_rate", "total_shots"],
        ascending=[False, False],
    ).iloc[0]

    return [
        shared._build_metric_card(
            "Total shots",
            shared._format_count(total_shots),
        ),
        shared._build_metric_card(
            "Total goals",
            shared._format_count(total_goals),
        ),
        shared._build_metric_card(
            "Overall conversion",
            f"{shared._format_decimal(overall_conversion, 1)}%",
        ),
        shared._build_metric_card(
            "Best interval",
            (
                f"{best_interval_row['interval']} "
                f"({shared._format_decimal(best_interval_row['conversion_rate'], 1)}%)"
            ),
        ),
    ]


def _build_chart(chart_id, figure):
    """Wrap a figure in a shared Dash graph component."""

    return dash.dcc.Graph(
        id=chart_id,
        figure=figure,
        config=shared.GRAPH_CONFIG,
        className="chart-graph",
        style=shared._build_graph_style(figure),
    )


def _build_chart_mode_radio():
    """Build the chart-mode radio control for RQ3."""

    return dash.dcc.RadioItems(
        id="rq3-chart-mode",
        options=[
            {
                "label": "Total counts",
                "value": "bar",
            },
            {
                "label": "Conversion rate",
                "value": "line",
            },
        ],
        value="bar",
        inline=True,
    )


RQ3_FRAME = _load_rq3_data()
RQ3_INTERVAL_SUMMARY = _build_interval_summary(RQ3_FRAME)
RQ3_BAR_FIGURE = _build_bar_figure(RQ3_INTERVAL_SUMMARY)
RQ3_LINE_FIGURE = _build_line_figure(RQ3_INTERVAL_SUMMARY)


def _build_page_slots():
    """Build the template slot content used by the RQ3 page."""

    return {
        "chip_shot_events": dash.html.Span(
            (
                f"{shared._format_count(len(RQ3_FRAME))} "
                "shot events"
            ),
            className="chip",
        ),
        "chip_intervals": dash.html.Span(
            (
                f"{shared._format_count(len(INTERVAL_LABELS))} "
                "time intervals"
            ),
            className="chip",
        ),
        "metrics": _build_metrics_cards(),
        "chart_mode_radio": _build_chart_mode_radio(),
        "main_chart": _build_chart(
            "rq3-main-chart",
            RQ3_BAR_FIGURE,
        ),
        "plot_description": _get_plot_description("bar"),
    }


def build_page():
    """Return the RQ3 layout for the Dash app."""

    return shared._load_html_template(
        RQ3_TEMPLATE_PATH,
        _build_page_slots(),
    )


def register_callbacks(app):
    """Register the RQ3 callbacks on the given Dash app."""

    @app.callback(
        dash.Output("rq3-main-chart", "figure"),
        dash.Output("rq3-main-chart", "style"),
        dash.Output("rq3-plot-description", "children"),
        dash.Input("rq3-chart-mode", "value"),
    )
    def _update_chart(chart_mode):
        """Refresh the chart and explanatory text when mode changes."""

        if chart_mode == "line":
            figure = RQ3_LINE_FIGURE
        else:
            figure = RQ3_BAR_FIGURE

        return (
            figure,
            shared._build_graph_style(figure),
            _get_plot_description(chart_mode),
        )
