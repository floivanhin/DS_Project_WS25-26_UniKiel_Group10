import soccerdata

understat = soccerdata.Understat(leagues="GER-Bundesliga", seasons="2024/2025")

schedule = understat.read_schedule()

schedule.to_csv("understat_schedule.csv", index=False, encoding="utf-8")
