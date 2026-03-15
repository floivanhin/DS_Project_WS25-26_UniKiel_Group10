# Import packages
from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import dash_daq as daq
import pandas as pd
import plotly.express as px

# Incorporate data
df_RQ8 = pd.read_csv("RQ3_RQ8\RQ8.csv")

# Average shots by number of subs box plot

avg_shots = df_RQ8[df_RQ8["sub_count"].isin([2, 3, 4, 5])]

fig_subCountBox = px.box(
    avg_shots, 
    x="sub_count", 
    y="total_shots_secondHalf",
    category_orders={"sub_count": [2, 3, 4, 5]},
    title="Total Number of Substitutions vs Average Shots on Goal in 2nd half",
    labels={
        "sub_count": "Number of Substitutions",
        "total_shots_secondHalf": "Average Number of Shots on Goal in 2nd half"
    },
    color_discrete_sequence=["#DED11D"]
)

fig_subCountBox.update_layout(
    width=1000,  
    height=600,   
    xaxis=dict(type="category"),
    plot_bgcolor="white",
    margin=dict(l=40, r=40, t=60, b=40) 
)

fig_subCountBox.update_yaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")

# Average shots by number of subs bar plot

avg_shots = df_RQ8[df_RQ8["sub_count"].isin([2, 3, 4, 5])].groupby("sub_count")["total_shots_secondHalf"].mean().reset_index()

fig_subCountBar = px.bar(
    avg_shots, 
    x="sub_count", 
    y="total_shots_secondHalf",
    title="Total Number of Substitutions vs Avarage Shots on Goal in 2nd half",
    labels={
        "sub_count": "Number of Substitutions",
        "total_shots_secondHalf": "Avarage Number of Shots on Goal in 2nd half"
    },
    color_discrete_sequence=["#02A508"],
    category_orders={"sub_count": [2, 3, 4, 5]}
)

fig_subCountBar.update_layout(
    width=800,
    height=400,
    xaxis=dict(type="category"),
    yaxis=dict(showgrid=True, gridcolor="LightGray"),
    plot_bgcolor="white",
    margin=dict(l=40, r=40, t=60, b=40)
)

fig_subCountBar.update_xaxes(
    showline=True, 
    linewidth=1, 
    linecolor="black", 
    type="category" 
)

fig_subCountBar.update_yaxes(
    showline=True, 
    linewidth=1, 
    linecolor="black", 
    showgrid=True, 
    gridcolor="LightGray"
)

# Substitution timing vs. shots on goal

shot_diff_df = df_RQ8[(df_RQ8["avg_sub"] > 55) & (df_RQ8["avg_sub"] < 80)].copy()

aggregated_shotDiff_df = shot_diff_df.groupby(shot_diff_df["avg_sub"].round())["spm_diff"].mean()

df_sub_timing = aggregated_shotDiff_df.reset_index()
df_sub_timing.columns = ["avg_sub", "spm_diff"]

fig_timing = px.line(
    df_sub_timing, 
    x="avg_sub", 
    y="spm_diff",
    title="Substitution timing vs. Change in shots per minute in the 2nd half",
    markers=True
)

fig_timing.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
fig_timing.update_traces(line_color="#441AEE", line_width=2, marker=dict(size=8))
fig_timing.update_layout(
    template="plotly_white",
    xaxis_title="Average Minute of Substitution",
    yaxis_title="Change in Shots Per Minute (After _ Before)"
)

# Number of minutes played by substituted players vs. shots on goal

aggregated_subMin_df = df_RQ8.groupby(df_RQ8["total_sub_time"].round())["total_shots_secondHalf"].mean()


def fig_minutes(smoothed_data):
    smoothed_data = smoothed_data.reset_index()

    fig_minutes = px.line(
        smoothed_data, 
        x="total_sub_time", 
        y="total_shots_secondHalf",
        markers=True,
        title="Total number of minutes played by substituted players vs Shots on Goal in 2nd half (Smoothed)",
        labels={
            "total_sub_time": "Number of minutes played by substituted players",
            "total_shots_secondHalf": "Shots on Goal in 2nd half"
        }
    )

    fig_minutes.update_traces(
        line=dict(color="#441AEE", width=2),
        marker=dict(size=6)
    )

    fig_minutes.update_layout(
        width=1000, 
        height=600,
        plot_bgcolor="white",
        margin=dict(l=50, r=50, t=80, b=50)
    )

    fig_minutes.update_xaxes(
        showline=True,
        linewidth=1,
        linecolor="black",
        showgrid=True,
        gridcolor="rgba(211, 211, 211, 0.3)"
    )

    fig_minutes.update_yaxes(
        showline=True,
        linewidth=1,
        linecolor="black",
        showgrid=True,
        gridcolor="rgba(211, 211, 211, 0.3)"
    )
    return fig_minutes

# Initialize app
app = Dash()

# App layout
app.layout = [
    html.Div(children=
             "Research Question 8:  How do the number and average timing of substitutions affect the number of shots on goal in the second half?"),
    html.Hr(),
    html.Div([
        html.Label("Select Analysis View:"),
        dcc.RadioItems(
            id="main_selector",
            options=[
                {"label": "Number of substitutions", "value": "number"},
                {"label": "Substituion timing", "value": "timing"},
                {"label": "Minutes Played", "value": "minutes"}
            ],
            value="number",
            inline=True
        ),
    ], style={"padding": "10px", "backgroundColor": "#f9f9f9"}),
    html.Hr(),
    html.Div([
        # Toggle for Plot 1
        html.Div([
            html.Label("Plot Type: "),
            daq.BooleanSwitch(id="type_toggle", on=True, label="Toggle View (Barplot vs. Boxplot)", labelPosition="left")
        ], id="toggle_container", style={"display": "none"}),

        # Slider for Plot 3
        html.Div([
            html.Label("Rolling Window Size:"),
            dcc.Slider(id="window_slider", min=2, max=20, step=1, value=10, 
                       marks={i: str(i) for i in range(2, 21, 2)})
        ], id="slider_container", style={"display": "none"})
    ], style={"padding": "20px"}),
    html.Div(id="plot_description", style={"marginTop": "20px", "fontWeight": "bold", "fontSize": "18px"}),
    dcc.Graph(id="main_graph")
]

@callback(
    Output("toggle_container", "style"),
    Output("slider_container", "style"),
    Input("main_selector", "value")
)
def toggle_controls(view):
    toggle_style = {"display": "block"} if view == "number" else {"display": "none"}
    slider_style = {"display": "block"} if view == "minutes" else {"display": "none"}
    return toggle_style, slider_style

@callback(
    Output("main_graph", "figure"),
    Output("plot_description", "children"),
    Input("main_selector", "value"),
    Input("type_toggle", "on"),
    Input("window_slider", "value")
)
def update_graph(view, toggle, window_size):
    if view == "number":
        if toggle == True:
            fig = fig_subCountBar
        else:
            fig = fig_subCountBox
        desc = "Average shots on goal in 2nd half by number of substitutions by a team"

    elif view == "timing":
        fig = fig_timing
        desc = "Minute of the average substitution by a team during a game vs. their shots on goal in the 2nd half"

    else:
        smoothed = aggregated_subMin_df.rolling(window=window_size, center=True, min_periods=2).mean().reset_index()
        fig = fig_minutes(smoothed)
        desc = "Cumulated number of minutes played by substituted players vs. shots on goal in 2nd (data smoothed with rolling avg with adjustable rolling window size)"

    return fig, desc


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
