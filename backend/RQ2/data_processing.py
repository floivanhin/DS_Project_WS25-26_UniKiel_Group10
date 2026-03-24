import pandas as pd

seasons = ['2020-2021','2021-2022','2022-2023','2023-2024','2024-2025']
data_list = []
matchday = 1
csv_data = []

for i in seasons:
    df = pd.read_csv('data_'+i+'.csv')

    game_counter = 0
    goals = 0
    r = []
    for i in range (306):
        goals = goals + df["away_goals"][i] + df["home_goals"][i]
        game_counter += 1
        if game_counter > 8:
            game_counter = 0
            r = r + [goals]
            goals = 0
    data_list = data_list + [r]


for i in range(34):
    csv_data = csv_data + [[matchday, data_list[0][i], data_list[1][i], data_list[2][i], data_list[3][i], data_list[4][i]]]
    matchday += 1


   
tup = pd.DataFrame(csv_data, columns=['matchday', 'total_goals_2020-2021','total_goals_2021-2022','total_goals_2022-2023','total_goals_2023-2024','total_goals_2024-2025'])
tup.to_csv("data_goals.csv", index=False, encoding="utf-8")
