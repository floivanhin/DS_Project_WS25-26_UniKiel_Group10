# Import packages
from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import pandas as pd
import plotly.express as px

# Incorporate data
df_RQ3 = pd.read_csv("RQ3_RQ8\RQ3.csv")


# Making the bar plot
# Defining intervalls
bins = [0, 10, 15, 20, 25, 30, 35, 40, 45, 50, float("inf")]
labels = ["0-10s", "10-15s", "15-20s", "20-25s", "25-30s", "30-35s", "35-40s", "40-45s", "45-50s", "50s+"]

# Assigning intervalls to each element of the dataframe
df_RQ3["intervalls"] = pd.cut(
    df_RQ3["time_delta"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

goals = []
no_goals = []

for label in labels:
    subset = df_RQ3[df_RQ3["intervalls"] == label]

    g = int(subset[subset["is_goal"]==True].shape[0])
    ng = int(subset[subset["is_goal"] == False].shape[0])

    goals.append(g)
    no_goals.append(ng)

plot_data = pd.DataFrame({
    "Interval": labels + labels,
    "Count": no_goals + goals,
    "Outcome": ["No Goal"] * len(labels) + ["Goal"] * len(labels)
})

fig_bar = px.bar(
    plot_data, 
    x="Interval", 
    y="Count", 
    color="Outcome",
    color_discrete_map={"No Goal": "#FF0000", "Goal": "#27ae60"}, 
    title="Shots and Goals by Transition Time"
)

fig_bar.update_layout(
    template="plotly_white",
    barmode="stack",
    legend_title_text="Result",
    xaxis={"categoryorder": "array", "categoryarray": labels}
)

# Making the line plot
percentages = []
for x in range(len(goals)):
    percentages.append(round(goals[x]/(no_goals[x]+goals[x])*100))

df_line = pd.DataFrame({
    "Interval": labels,
    "Conversion Rate (%)": percentages
})

fig_line = px.line(
    df_line, 
    x="Interval", 
    y="Conversion Rate (%)",
    title="Goal Conversion Rate per Time Interval",
    markers=True,
)

fig_line.update_traces(
    line_color="#27ae60",
    line_width=2,
    marker=dict(size=8)
)

fig_line.update_layout(
    template="plotly_white",
    xaxis_title="Seconds after possession win",
    yaxis_title="Conversion Rate (%)",
    xaxis={"categoryorder": "array", "categoryarray": labels},
    width=1000, 
    height=500
)

# Initialize the app
app = Dash()

# App layout
app.layout = [
    html.Div(children=
             "Research Question 3:  How does the time between winning possession in your own half and the first shot correlate with the probability of scoring (per shot)?"),
    html.Hr(),
    dcc.RadioItems(
        options=[
            {"label": "Total Counts", "value": "bar"},
            {"label": "Conversion Rate", "value": "line"}
        ],
        value="bar",
        id="controls_and_radio_item",
        inline=True
    ),
    html.Div(id="plot_description", style={"marginTop": "20px", "fontWeight": "bold", "fontSize": "18px"}),
    dcc.Graph(id="main_graph")
]

@callback(
    Output("main_graph", "figure"),
    Output("plot_description", "children"),
    Input("controls_and_radio_item", "value")
)
def update_graph(selection):
    if selection == "bar":
        fig = fig_bar
        desc = "Amount of shots and goals that happened after a team gained possession in its own half based on the time it took between winning possession and shooting."
    else:
        fig = fig_line
        desc = "Percentage of shots that turned into goals based on the time it took for a team between winning possession in its own half and shooting"
    
    fig.update_layout(xaxis={"categoryorder": "array", "categoryarray": labels})

    return fig, desc

# Run the app
if __name__ == "__main__":
    app.run(debug=True)