# DS_Project_WS25-26_UniKiel_Group10

Group 10 data science project for the University of Kiel, winter semester 2025/2026.

## Topic

This project is about football data from the Bundesliga 2024/2025 season.

Some research questions are split across different folders.

## Main folders

- `RQ1/`
- `RQ2/`
- `RQ3_RQ8/`
- `RQ4_RQ8/`
- `RQ5/`
- `RQ7/`
- `my-vue-app/`
- `Topics.md`

## RQ4 and RQ8

The folder `RQ4_RQ8/` contains the code for these two questions:

- `RQ4`: Which players do better at home and which do better away?
- `RQ8`: How does average age relate to team efficiency (`goals per shot`)?

### Files in `RQ4_RQ8`

- `main.py`
  - runs the whole workflow
- `espn_data_download_pipeline.py`
  - builds the raw ESPN table for RQ8
- `whoscored_data_download_pipeline.py`
  - builds the raw WhoScored table for RQ4
- `rq4_analysis.py`
  - builds the RQ4 result tables
- `rq8_analysis.py`
  - builds the RQ8 result tables

### How to run it

From `RQ4_RQ8/`:

```powershell
python main.py
```

### Important note

`main.py` does not use command line arguments anymore.

It always uses these fixed values:

- league: `GER-Bundesliga`
- season: `2425`
- refresh: `False`

So it will use the saved raw CSV files if they already exist.

## Output files

Raw CSV files go to:

`RQ4_RQ8/data/downloaded_outputs_to_analyse/`

Files:

- `espn_player_match_data_for_rq8.csv`
- `whoscored_player_match_data_for_rq4.csv`

Analysis CSV files go to:

`RQ4_RQ8/analysis_output/`

Files:

- `rq4/rq4_home_away_player_ratings.csv`
- `rq4/rq4_player_home_away_delta.csv`
- `rq8/rq8_team_age_vs_efficiency.csv`
- `rq8/rq8_player_age_profile.csv`
- `rq8/rq8_player_best_age.csv`
- `rq8/rq8_optimal_age_summary.csv`
