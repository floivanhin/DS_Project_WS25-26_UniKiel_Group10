"""Navbar module for the project web app.

This file exists to keep all top-navigation logic in one place:
- list of nav links (Overview + RQ1-RQ9)
- rendering of the clickable header/navbar component
"""

import dash


NAV_LINKS = [("/", "Overview")] + [
    (f"/rq{rq_number}", f"RQ{rq_number}")
    for rq_number in range(1, 10)
]


def build_navbar(pathname):
    """Return the top navigation bar component."""

    current_path = pathname or "/"
    if current_path == "/summary":
        current_path = "/"

    return dash.html.Header(
        className="topbar",
        children=[
            dash.html.Div(
                className="topbar-inner",
                children=[
                    dash.dcc.Link(
                        "Bundesliga Statistics",
                        href="/",
                        className="site-title",
                    ),
                    dash.html.Nav(
                        className="top-nav",
                        children=[
                            dash.dcc.Link(
                                label,
                                href=href,
                                className=(
                                    "nav-link active"
                                    if href == current_path
                                    else "nav-link"
                                ),
                            )
                            for href, label in NAV_LINKS
                        ],
                    ),
                ],
            )
        ],
    )
