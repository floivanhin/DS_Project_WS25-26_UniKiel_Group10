"""Build the text-only overview page for the Dash website.

Input: static project text.
Output: the Dash layout for the landing page.
"""

import dash


def build_page():
    """Return the overview layout for the Dash app."""

    return dash.html.Main(
        className="page",
        children=[
            dash.html.Section(
                className="hero",
                children=[
                    dash.html.Span("Project Overview", className="tag"),
                    dash.html.H1("Bundesliga 2024/25 Research Questions"),
                    dash.html.P(
                        (
                            "Goal: answer selected research questions with "
                            "reproducible data pipelines, analysis outputs, "
                            "and interactive Dash web pages."
                        ),
                        className="subtitle",
                    ),
                    dash.html.Div(
                        className="chips",
                        children=[
                            dash.html.Span(
                                "Bundesliga 2024/25",
                                className="chip",
                            ),
                            dash.html.Span(
                                "Reproducible pipelines",
                                className="chip",
                            ),
                            dash.html.Span(
                                "Analysis outputs",
                                className="chip",
                            ),
                            dash.html.Span(
                                "9 research questions",
                                className="chip",
                            ),
                        ],
                    ),
                ],
            ),
            dash.html.Section(
                className="content-grid",
                children=[
                    dash.html.Article(
                        className="panel span-12",
                        children=[
                            dash.html.H2("Research questions"),
                            dash.html.P(
                                (
                                    "This project investigates the following "
                                    "Bundesliga questions:"
                                )
                            ),
                            dash.html.Ul(
                                children=[
                                    dash.html.Li(
                                        (
                                            "RQ1: How does the weather affect "
                                            "the number of goals in a match?"
                                        )
                                    ),
                                    dash.html.Li(
                                        (
                                            "RQ2: How does the matchday affect "
                                            "the amount of goals?"
                                        )
                                    ),
                                    dash.html.Li(
                                        (
                                            "RQ3: How does the time between "
                                            "winning possession in your own "
                                            "half and the first shot correlate "
                                            "with the probability of scoring "
                                            "(per shot)?"
                                        )
                                    ),
                                    dash.html.Li(
                                        (
                                            "RQ4: Which players perform "
                                            "particularly well in home matches "
                                            "and which in away matches?"
                                        )
                                    ),
                                    dash.html.Li(
                                        (
                                            "RQ5: What is the relationship "
                                            "between payroll spending and "
                                            "league points?"
                                        )
                                    ),
                                    dash.html.Li(
                                        (
                                            "RQ6: How does the league position "
                                            "affect ticket prices?"
                                        )
                                    ),
                                    dash.html.Li(
                                        (
                                            "RQ7: What is the relationship "
                                            "between the number of spectators "
                                            "and the number of cards issued "
                                            "(for the home team) per foul?"
                                        )
                                    ),
                                    dash.html.Li(
                                        (
                                            "RQ8: How do the number and "
                                            "average timing of substitutions "
                                            "affect the number of shots on "
                                            "goal?"
                                        )
                                    ),
                                    dash.html.Li(
                                        (
                                            "RQ9: How does the average player "
                                            "age affect a team's efficiency "
                                            "(goals per shot)?"
                                        )
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            dash.html.P(
                (
                    "Use the navbar to navigate between overview and the "
                    "research-question routes."
                ),
                className="source-note",
            ),
            dash.html.Footer(
                (
                    "This overview summarizes the project goal and all "
                    "Bundesliga research questions."
                ),
                className="footer",
            ),
        ],
    )
