import soccerdata

seasons = ['2020/2021','2021/2022','2022/2023','2023/2024','2024/2025']

for i in seasons:
    understat = soccerdata.Understat(leagues='GER-Bundesliga', seasons=i)
    schedule = understat.read_schedule()
    schedule.to_csv('data_'+i[:4]+'-'+i[5:]+'.csv', index=False, encoding="utf-8")
