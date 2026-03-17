# Import packages
from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import pandas as pd
import plotly.express as px

# Incorporate data
df = pd.read_csv("data_goals.csv")

# Initialize the app
app = Dash()

# App layout
app.layout = [
    html.Div(children='Research Question 2: How does the matchday affect the amount of goals?'),
    html.Hr(),
    dcc.RadioItems(options=['bar', 'histogram', 'line'], value='bar', id='controls-and-radio-item'),
    dcc.Graph(figure={}, id='controls-and-graph')
]

@callback(
    Output(component_id='controls-and-graph', component_property='figure'),
    Input(component_id='controls-and-radio-item', component_property='value')
)
# , labels={'total_goals_2020-2021': 'goals','total_goals_2021-2022': 'goals','total_goals_2022-2023': 'goals','total_goals_2023-2024': 'goals','total_goals_2024-2025': 'goals'}
def update_graph(col_chosen):
    if col_chosen == 'bar':
        fig = px.bar(df, x='matchday', y=['total_goals_2020-2021','total_goals_2021-2022','total_goals_2022-2023','total_goals_2023-2024','total_goals_2024-2025'])
        fig.update_layout(yaxis_title='goals')
    if col_chosen == 'histogram':
        fig = px.histogram(df, x='matchday', y=['total_goals_2020-2021','total_goals_2021-2022','total_goals_2022-2023','total_goals_2023-2024','total_goals_2024-2025'])
        fig.update_layout(yaxis_title='goals')
    if col_chosen == 'line':
        fig = px.line(df, x='matchday', y=['total_goals_2020-2021','total_goals_2021-2022','total_goals_2022-2023','total_goals_2023-2024','total_goals_2024-2025'])
        fig.update_layout(yaxis_title='goals')
    return fig

if __name__ == '__main__':
    app.run(debug=True)