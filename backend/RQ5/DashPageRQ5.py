# Import packages
from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import pandas as pd
import plotly.express as px

# Incorporate data
df = pd.read_csv("budget.csv")


# Initialize the app
app = Dash()

# App layout
app.layout = [
    html.Div(children='Research Question 5: What is the relationship between payroll spending and league points?'),
    html.Hr(),
    dcc.RadioItems(options=['budget', 'budget_rank'], value='budget', id='controls-and-radio-item'),
    dcc.Graph(figure={}, id='controls-and-graph')
]

@callback(
    Output(component_id='controls-and-graph', component_property='figure'),
    Input(component_id='controls-and-radio-item', component_property='value')
)

def update_graph(col_chosen):
    if col_chosen == 'budget':
        fig = px.scatter(df, x = 'budget(€)', y = ['points','league_position'], hover_name='club', labels={"category": "Group"})
    if col_chosen == 'budget_rank':
        fig = px.scatter(df, x = 'budget_rank', y = ['points','league_position'], hover_name='club', labels={"category": "Group"})
    return fig

if __name__ == '__main__':
    app.run(debug=True)
    