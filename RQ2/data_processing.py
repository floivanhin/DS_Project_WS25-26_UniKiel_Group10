import pandas as pd

df = pd.read_csv("understat_schedule.csv")

c = 0
b = 0
r = []
for i in range (306):
    b = b + df["away_goals"][i] + df["home_goals"][i]
    c += 1
    if c > 8:
        c = 0
        r = r + [b]
        b = 0
    else:
        pass

x = 1
y = []
for i in r:
    y = y + [[x, i]]
    x += 1

tup = pd.DataFrame(y, columns=['matchday', 'total_goals'])
tup.to_csv("RQ2.csv", index=False, encoding="utf-8")
