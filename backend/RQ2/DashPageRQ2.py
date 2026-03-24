# Import packages
from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import pandas as pd
import plotly.express as px

# Incorporate data
#df_RQ3 = pd.read_csv("RQ3_RQ8/RQ3.csv")
df = pd.read_csv("data_goals.csv")

# Initialize the app
app = Dash()

# App layout
app.layout = [
    html.Div(children='Research Question 2: How does the matchday affect the amount of goals?'),
    #dag.AgGrid(
    #    rowData=df.to_dict('records'),
    #    columnDefs=[{"field": i} for i in df.columns]
    #), 
    dcc.Graph(figure=px.bar(df, x='matchday', y=['total_goals_2020-2021','total_goals_2021-2022','total_goals_2022-2023','total_goals_2023-2024','total_goals_2024-2025']))

]

if __name__ == '__main__':
    app.run(debug=True)