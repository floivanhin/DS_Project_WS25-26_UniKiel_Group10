"""Run the folder-based Dash website for the Bundesliga project.

Input: shared Dash page modules, local RQ CSV outputs, and raw source CSVs.
Output: a routed Dash app with separated page modules per folder.
"""

import importlib.util
import pathlib
import subprocess
import sys


REQUIRED_MODULES = ("dash", "plotly", "pandas")


def _install_dash_dependencies():
    """Install required Dash dependencies if they are missing."""

    from pathlib import Path

    requirements_path = Path(__file__).resolve().parent / "requirements.txt"
    missing_modules = [
        module_name
        for module_name in REQUIRED_MODULES
        if importlib.util.find_spec(module_name) is None
    ]
    if not missing_modules:
        return

    print(
        "Installing missing Dash app dependencies for this interpreter: "
        f"{', '.join(missing_modules)}"
    )

    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements_path),
            ]
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Automatic dependency installation failed. Run "
            f"`{sys.executable} -m pip install -r {requirements_path}`."
        ) from error


_install_dash_dependencies()

import dash

import Dash_Webapp.navbar as navbar
import Dash_Webapp.overview.page as overview_page
import Dash_Webapp.shared as shared
import RQ4_RQ9.dash_page_rq4.page as rq4_page
import RQ4_RQ9.dash_page_rq9.page as rq9_page


PAGE_BUILDERS = {
    "/": overview_page.build_page,
    "/summary": overview_page.build_page,
    "/rq4": rq4_page.build_page,
    "/rq9": rq9_page.build_page,
}
UNIMPLEMENTED_RQ_ROUTES = {
    "/rq1",
    "/rq2",
    "/rq3",
    "/rq5",
    "/rq6",
    "/rq7",
    "/rq8",
}

APP_ROOT = pathlib.Path(__file__).resolve().parent

app = dash.Dash(
    __name__,
    assets_folder=str(APP_ROOT / "Dash_Webapp" / "assets"),
    suppress_callback_exceptions=True,
    title="Bundesliga Statistics",
)
server = app.server


def _serve_layout():
    """Return the root Dash layout shell."""

    return dash.html.Div(
        children=[
            dash.dcc.Location(id="url"),
            dash.html.Div(id="app-shell"),
        ]
    )


app.layout = _serve_layout
rq4_page.register_callbacks(app)
rq9_page.register_callbacks(app)


def _build_blank_page():
    """Return an intentionally blank page shell."""

    return dash.html.Main(className="page")


@app.callback(
    dash.Output("app-shell", "children"),
    dash.Input("url", "pathname"),
)
def _render_page(pathname):
    """Build the page content for the current route."""

    current_path = pathname or "/"
    page_builder = PAGE_BUILDERS.get(current_path)
    if page_builder is not None:
        page = page_builder()
    elif current_path in UNIMPLEMENTED_RQ_ROUTES:
        page = _build_blank_page()
    else:
        page = shared._build_not_found_page()

    return [
        navbar.build_navbar(pathname),
        page,
    ]


if __name__ == "__main__":
    app.run(debug=False)
