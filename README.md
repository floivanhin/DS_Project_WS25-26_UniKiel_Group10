# DS_Project_WS25-26_UniKiel_Group10

This repository contains the Data Science Project of Group 10 for the
University of Kiel, Winter Semester 2025/2026.

## Dash Web App (Current Flow)

The project now includes a root-level Dash app entrypoint:

- `app.py`
  - main router and Dash startup
- `requirements.txt`
  - dependencies for the Dash web app

### What The Dash App Shows

- `Overview` page (project landing page)
- `RQ4` page (home vs away player performance analysis)
- `RQ9` page (age vs team efficiency analysis)
- Navbar links for `RQ1` to `RQ9`
  - currently `RQ1-3` and `RQ5-8` load blank placeholder pages

### Dash App Structure

- `Dash_Webapp/`
  - `assets/` (global CSS)
  - `overview/` (overview page module)
  - `navbar.py` (navbar links and rendering)
  - `shared.py` (shared template/data formatting helpers)
  - `styling.py` (shared chart/style constants and helpers)
- `RQ4_RQ9/dash_page_rq4/`
  - RQ4 Dash page logic, template, and RQ4 analysis CSVs
- `RQ4_RQ9/dash_page_rq9/`
  - RQ9 Dash page logic, template, and RQ9 analysis CSVs
- `RQ4_RQ9/data/downloaded_outputs_to_analyse/`
  - raw source CSVs consumed by RQ4 and RQ9 page data loaders

### How To Run The Dash Web App

From repository root:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Then open:

- `http://127.0.0.1:8050/`

## Project Scope

- Topic area: Football
- Season scope: Bundesliga 2024/2025
- Goal: answer selected research questions with reproducible data pipelines,
  analysis outputs, and interactive Dash web pages

## Repository Structure

- `app.py`
  - root Dash app entrypoint and route wiring
- `requirements.txt`
  - Python dependencies for the Dash web app
- `Dash_Webapp/`
  - shared Dash web app shell logic (navbar, styling, overview, assets)
- `RQ1/`
  - work related to Research Question 1
- `RQ2/`
  - work related to Research Question 2
- `RQ3_RQ8/`
  - work related to Research Questions 3 and 8
- `RQ4_RQ9/`
  - pipeline and analysis code for Research Questions 4 and 9
- `RQ5/`
  - work related to Research Question 5
- `RQ7/`
  - work related to Research Question 7
- `Topics.md`
  - full list of project topics and research questions

## RQ4 And RQ9 Analysis

- Contributor: Cat Lam Tang
- Folder: `RQ4_RQ9/`
- Research Question 4:
  - Which players perform particularly well in home matches and which in away
    matches?
- Research Question 9:
  - How does the average player age affect a team's efficiency (goals per
    shot)?

### What This Part Contains

- `RQ4_RQ9/main.py`
  - runs the full workflow
  - loads cached raw outputs or rebuilds them
  - writes raw CSV files, derived analysis CSV files, and terminal summaries
- `RQ4_RQ9/pipeline_config.py`
  - parses command line arguments
  - builds the pipeline configuration
  - prepares shared environment settings
- `RQ4_RQ9/pipeline_utils.py`
  - stores shared constants and helper functions
- `RQ4_RQ9/espn_data_download_pipeline.py`
  - builds the ESPN dataset used for RQ9
- `RQ4_RQ9/whoscored_data_download_pipeline.py`
  - builds the WhoScored dataset used for RQ4
- `RQ4_RQ9/rq4_analysis.py`
  - builds the home-vs-away rating tables for RQ4
- `RQ4_RQ9/rq9_analysis.py`
  - builds the age and efficiency tables for RQ9

### How To Run

From `RQ4_RQ9/`:

```powershell
python main.py
```

### Outputs

Raw source datasets are written to `RQ4_RQ9/data/downloaded_outputs_to_analyse/`:

- `espn_player_match_data_for_rq9.csv`
  - one row per `match x team x player`
  - includes the fields needed for RQ9 such as `player`, `team`, `age`,
    `player_goals`, `player_shots`, `team_goals`, and `team_shots`
- `whoscored_player_match_data_for_rq4.csv`
  - one row per `match x player`
  - includes the fields needed for RQ4 such as `player`, `team`,
    `home_away`, `overall_rating`, `is_starting_xi`, and
    `is_man_of_the_match`

Derived analysis CSVs used by the Dash pages are stored under:

- `RQ4_RQ9/dash_page_rq4/analysis_diagram_data/`
- `RQ4_RQ9/dash_page_rq9/analysis_diagram_data/`
