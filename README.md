# DS_Project_WS25-26_UniKiel_Group10

This repository contains the Data Science Project of Group 10 for the
University of Kiel, Winter Semester 2025/2026.

## Project Scope

- Topic area: Football
- Season scope: Bundesliga 2024/2025
- Goal: answer selected research questions with reproducible data pipelines,
  analysis outputs, and documentation pages in `docs/`

## Repository Structure

- `RQ1/`
  - work related to Research Question 1
- `RQ3_RQ8/`
  - work related to Research Questions 3 and 8
- `RQ4_RQ8/`
  - pipeline and analysis code for Research Questions 4 and 8
- `RQ7/`
  - work related to Research Question 7
- `docs/`
  - website files and generated analysis CSVs used by the project pages
- `Topics.md`
  - full list of project topics and research questions

## RQ4 And RQ8 Analysis

- Contributor: Cat Lam Tang
- Folder: `RQ4_RQ8/`
- Research Question 4:
  - Which players perform particularly well in home matches and which in away
    matches?
- Research Question 8:
  - How does the average player age affect a team's efficiency (goals per
    shot)?

### What This Part Contains

- `RQ4_RQ8/main.py`
  - runs the full workflow
  - loads cached raw outputs or rebuilds them
  - writes raw CSV files, derived analysis CSV files, and terminal summaries
- `RQ4_RQ8/pipeline_config.py`
  - parses command line arguments
  - builds the pipeline configuration
  - prepares shared environment settings
- `RQ4_RQ8/pipeline_utils.py`
  - stores shared constants and helper functions
- `RQ4_RQ8/espn_data_download_pipeline.py`
  - builds the ESPN dataset used for RQ8
- `RQ4_RQ8/whoscored_data_download_pipeline.py`
  - builds the WhoScored dataset used for RQ4
- `RQ4_RQ8/rq4_analysis.py`
  - builds the home-vs-away rating tables for RQ4
- `RQ4_RQ8/rq8_analysis.py`
  - builds the age and efficiency tables for RQ8

### How To Run

From `RQ4_RQ8/`:

```powershell
python main.py
```

### Outputs

Raw source datasets are written to `RQ4_RQ8/data/downloaded_outputs_to_analyse/`:

- `espn_player_match_data_for_rq8.csv`
  - one row per `match x team x player`
  - includes the fields needed for RQ8 such as `player`, `team`, `age`,
    `player_goals`, `player_shots`, `team_goals`, and `team_shots`
- `whoscored_player_match_data_for_rq4.csv`
  - one row per `match x player`
  - includes the fields needed for RQ4 such as `player`, `team`,
    `home_away`, `overall_rating`, `is_starting_xi`, and
    `is_man_of_the_match`

