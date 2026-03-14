"""Styling module for shared visual configuration.

This file exists to centralize visual defaults used across pages:
- global color palette and graph config
- reusable Plotly figure styling helpers
- reusable empty-figure placeholder helper
"""

import plotly.graph_objects as go


GRAPH_CONFIG = {"displayModeBar": False, "responsive": True}
COLORS = {
    "red": "#d20515",
    "red_dark": "#980211",
    "red_soft": "#ffe8eb",
    "surface": "#ffffff",
    "border": "#dfdfdf",
    "text": "#1f1f1f",
    "muted": "#646464",
    "grid": "#ececec",
    "neutral": "#575757",
    "neutral_light": "#9b9b9b",
}


def _get_figure_height(figure, default_height=420):
    """Return the pixel height configured on a Plotly figure."""

    layout_height = getattr(figure.layout, "height", None)
    if layout_height is None:
        return int(default_height)

    return int(layout_height)


def _build_graph_style(figure, default_height=420):
    """Return inline graph style that matches the figure height."""

    height = _get_figure_height(
        figure,
        default_height=default_height,
    )
    return {
        "height": f"{height}px",
        "width": "100%",
    }


def _apply_base_layout(figure, height=360):
    """Apply the shared chart styling to a Plotly figure."""

    figure.update_layout(
        height=height,
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor=COLORS["surface"],
        margin={"l": 18, "r": 18, "t": 40, "b": 18},
        font={
            "family": '"Barlow", "Trebuchet MS", sans-serif',
            "color": COLORS["text"],
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
    )
    figure.update_xaxes(
        showline=True,
        linecolor=COLORS["border"],
        gridcolor=COLORS["grid"],
        zeroline=False,
    )
    figure.update_yaxes(
        showline=True,
        linecolor=COLORS["border"],
        gridcolor=COLORS["grid"],
        zeroline=False,
    )
    return figure


def _build_empty_figure(message, height=320):
    """Create a placeholder chart that shows a message instead of data."""

    figure = go.Figure()
    figure.add_annotation(
        text=message,
        showarrow=False,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        font={"size": 15, "color": COLORS["muted"]},
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return _apply_base_layout(figure, height=height)
