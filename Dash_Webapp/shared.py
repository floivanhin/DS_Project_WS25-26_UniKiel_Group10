"""Store shared Dash helpers, constants, and styling utilities.

Input: generic formatting values, figure objects, and HTML templates.
Output: reusable layout, formatting, plotting, and template helpers.
"""

import functools
import pathlib
import xml.etree.ElementTree as element_tree

import dash
import pandas as pd

from Dash_Webapp.styling import COLORS
from Dash_Webapp.styling import GRAPH_CONFIG
from Dash_Webapp.styling import _apply_base_layout
from Dash_Webapp.styling import _build_empty_figure
from Dash_Webapp.styling import _build_graph_style
from Dash_Webapp.styling import _get_figure_height


APP_ROOT = pathlib.Path(__file__).resolve().parent
# Only the tags used in the local HTML fragments need a Dash mapping.
TEMPLATE_COMPONENTS = {
    "article": dash.html.Article,
    "div": dash.html.Div,
    "footer": dash.html.Footer,
    "h1": dash.html.H1,
    "h2": dash.html.H2,
    "h3": dash.html.H3,
    "label": dash.html.Label,
    "li": dash.html.Li,
    "main": dash.html.Main,
    "p": dash.html.P,
    "section": dash.html.Section,
    "span": dash.html.Span,
    "ul": dash.html.Ul,
}
TEMPLATE_ATTRIBUTE_MAP = {
    "class": "className",
    "for": "htmlFor",
}


def _build_metric_card(label, value, value_id=None):
    """Create one small card that shows a label and a value."""

    if value_id is None:
        value_node = dash.html.Div(value, className="metric-value")
    else:
        value_node = dash.html.Div(
            value,
            id=value_id,
            className="metric-value",
        )

    return dash.html.Article(
        className="metric",
        children=[
            dash.html.Div(label, className="metric-label"),
            value_node,
        ],
    )


@functools.lru_cache(maxsize=None)
def _read_html_template(template_path):
    """Return the cached HTML template string.

    Input: string path to a local HTML template file.
    Output: template contents as a UTF-8 string.
    """

    return pathlib.Path(template_path).read_text(encoding="utf-8")


def _collapse_template_text(text):
    """Normalize template whitespace for Dash text nodes.

    Input: raw text extracted from the HTML template.
    Output: single-spaced text or `None` if the text is empty.
    """

    if text is None:
        return None

    collapsed = " ".join(text.split())
    if collapsed == "":
        return None

    return collapsed


def _append_template_child(children, child_value):
    """Append one rendered template child to the target list.

    Input: destination list and one child value or child list.
    Output: the destination list updated in place.
    """

    if child_value is None:
        return

    if isinstance(child_value, (list, tuple)):
        for item in child_value:
            _append_template_child(children, item)
        return

    children.append(child_value)


def _build_template_children(element, slot_components):
    """Build the rendered children for one template element.

    Input: parsed XML element and slot-to-component mapping.
    Output: list of Dash child nodes for the current element.
    """

    children = []
    _append_template_child(
        children,
        _collapse_template_text(element.text),
    )

    for child in element:
        _append_template_child(
            children,
            _build_template_component(child, slot_components),
        )
        _append_template_child(
            children,
            _collapse_template_text(child.tail),
        )

    return children


def _build_template_component(element, slot_components):
    """Convert one HTML template element into a Dash component.

    Input: parsed XML element and slot-to-component mapping.
    Output: Dash component, text node, or slot replacement content.
    """

    # Example: <slot name="compare_graph" /> is replaced by the object from
    # slot_components["compare_graph"], such as a Dash dcc.Graph created in Python.
    if element.tag == "slot":
        slot_name = element.attrib.get("name")
        if not slot_name:
            raise ValueError(
                "Template slot is missing the required 'name' attribute."
            )
        if slot_name not in slot_components:
            raise KeyError(
                f"Template slot '{slot_name}' has no mapped content."
            )
        return slot_components[slot_name]

    component_class = TEMPLATE_COMPONENTS.get(element.tag)
    if component_class is None:
        raise ValueError(
            f"Unsupported HTML template tag: '{element.tag}'."
        )

    component_props = {
        TEMPLATE_ATTRIBUTE_MAP.get(name, name): value
        for name, value in element.attrib.items()
    }
    children = _build_template_children(element, slot_components)
    if children:
        if len(children) == 1:
            component_props["children"] = children[0]
        else:
            component_props["children"] = children

    return component_class(**component_props)


def _load_html_template(template_path, slot_components):
    """Load an HTML fragment and convert it into Dash components.

    Input: local template path and slot-to-component mapping.
    Output: rendered Dash component tree for the template root element.
    """

    # This is the step that turns the HTML template plus slot mapping into
    # the final Dash layout tree returned by the page module.
    template_file = pathlib.Path(template_path).resolve()
    try:
        template_root = element_tree.fromstring(
            _read_html_template(str(template_file))
        )
    except element_tree.ParseError as error:
        raise ValueError(
            f"Invalid HTML template syntax in {template_file}."
        ) from error

    return _build_template_component(template_root, slot_components)


def _format_decimal(value, digits=2):
    """Format a number with decimal places or return `n/a`."""

    if pd.isna(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def _format_signed(value, digits=3):
    """Format a signed number or return `n/a`."""

    if pd.isna(value):
        return "n/a"
    return f"{float(value):+.{digits}f}"


def _format_count(value):
    """Format a whole-number count or return `n/a`."""

    if pd.isna(value):
        return "n/a"
    return f"{int(round(float(value))):,}"


def _build_trend_line(frame, x_key, y_key):
    """Create a simple straight trend line from the given data."""

    if len(frame) < 2:
        return pd.DataFrame(columns=[x_key, y_key])

    sum_x = frame[x_key].sum()
    sum_y = frame[y_key].sum()
    sum_xy = (frame[x_key] * frame[y_key]).sum()
    sum_xx = (frame[x_key] * frame[x_key]).sum()
    n_points = len(frame)
    denominator = (n_points * sum_xx) - (sum_x * sum_x)

    if denominator == 0:
        return pd.DataFrame(columns=[x_key, y_key])

    slope = ((n_points * sum_xy) - (sum_x * sum_y)) / denominator
    intercept = (sum_y - (slope * sum_x)) / n_points
    min_x = frame[x_key].min()
    max_x = frame[x_key].max()

    return pd.DataFrame(
        {
            x_key: [min_x, max_x],
            y_key: [
                (slope * min_x) + intercept,
                (slope * max_x) + intercept,
            ],
        }
    )


def _build_not_found_page():
    """Build the fallback page for unknown routes."""

    return dash.html.Main(
        className="page",
        children=[
            dash.html.Section(
                className="hero",
                children=[
                    dash.html.Span("Page not found", className="tag"),
                    dash.html.H1("This route is not part of the Dash app."),
                    dash.html.P(
                        (
                            "Use the navigation above to return to the "
                            "overview or one of the research-question pages."
                        ),
                        className="subtitle",
                    ),
                ],
            )
        ],
    )
