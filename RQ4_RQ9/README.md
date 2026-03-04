# Bundesliga Player Average Age Metrics

This project analyzes Bundesliga squad age structure across seasons and links age to team shooting efficiency.

It is currently fixed to season `2425` (2024/25) and saves both intermediate caches and final CSV outputs.

## What This Project Does

- Loads player/team data for each configured season.
- Computes:
  - team-level average ages
  - season/global age summaries
  - RQ9: age vs. goal efficiency (`goals_per_shot`)
  - RQ9: estimated optimal age (quadratic fit, where possible)
  - RQ9: player age-band efficiency profile and best-performing age bands
  - RQ4 (new): home vs away player performance using WhoScored overall ratings
- Uses cache-first fetching:
  - reuses cached data if available
  - only polls missing data (unless `--refresh` is set)
- Prints progress bars for data loading and polling steps.

## Run

```powershell
python main.py
```

Common options:

```powershell
python main.py --refresh
python main.py --seasons 2425
python main.py --source-priority espn
python main.py --player-cache-dir ./data/player_cache --output-dir ./data/outputs
```

## Data and Caching

- Player/match cache: `data/player_cache/`
- soccerdata cache: `.soccerdata_cache/`
- Final outputs: `data/outputs/`

The script is designed to avoid unnecessary API calls and now reports what is completed vs what is still left to poll.

## Output Files

CSV outputs are grouped by question:

- `data/outputs/core/`
  - `bundesliga_team_player_ages.csv`
  - `bundesliga_team_age_summary.csv`
  - `bundesliga_season_age_summary.csv`
  - `bundesliga_global_age_summary.csv`
- `data/outputs/rq4/`
  - `rq4_home_away_player_ratings.csv`
  - `rq4_player_home_away_delta.csv`
- `data/outputs/rq9/`
  - `rq9_team_age_vs_efficiency.csv`
  - `rq9_team_match_efficiency.csv`
  - `rq9_optimal_age_summary.csv`
  - `rq9_player_age_profile.csv`
  - `rq9_player_best_age.csv`

Recommended CSVs for insightful charts:

- RQ4:
  - `rq4_player_home_away_delta.csv` for dumbbell charts / delta bar charts (home vs away effect per player).
  - `rq4_home_away_player_ratings.csv` for ranked home/away leaderboards.
- RQ9:
  - `rq9_team_age_vs_efficiency.csv` for team-level scatter plots (`avg_age` vs `goals_per_shot`).
  - `rq9_team_match_efficiency.csv` for match-level distributions and variance plots.
  - `rq9_player_age_profile.csv` for age-band efficiency curves.

## RQ4 Data and Answer (`data/outputs/rq4`)

### `rq4_home_away_player_ratings.csv`

- Meaning: one row per `season x player x home_away` with aggregated WhoScored ratings.
- Current size: `933` rows.
- Key columns:
  - `home_away`: split between `home` and `away`
  - `avg_overall_rating`, `median_overall_rating`, `best_overall_rating`, `worst_overall_rating`
  - `matches`, `starts`, `motm_awards`
  - `eligible_for_leaderboard`: `True` if `matches >= 5`

### `rq4_player_home_away_delta.csv`

- Meaning: one row per `season x player` with direct home-vs-away comparison.
- Current size: `481` rows.
- Key columns:
  - `home_avg_overall_rating`, `away_avg_overall_rating`
  - `avg_rating_delta_home_minus_away` (positive means better at home)
  - `abs_avg_rating_delta` (strength of difference, regardless of direction)
  - `eligible_both_sides`: enough matches on both sides (`>= 5` each)

### Answer to RQ4 (2024/25)

- Top average rating at home: `Omar Marmoush` (`8.270`, 8 matches).
- Top average rating away: `Omar Marmoush` (`8.201`, 9 matches).
- Across leaderboard-eligible rows (`matches >= 5`), mean home rating is slightly higher than away:
  - home: `6.614`
  - away: `6.578`
- Strongest positive home-vs-away deltas (only `eligible_both_sides=True`):
  - `Lucas Hoeler` `+0.785`
  - `Nico Schlotterbeck` `+0.773`
  - `Felix Nmecha` `+0.757`
- Strongest negative deltas (better away than home):
  - `Timo Horn` `-0.735`
  - `Jakov Medic` `-0.591`
  - `Nathan Ngoumou` `-0.588`

Conclusion: RQ4 indicates a small overall home advantage in player ratings, but with clear player-specific deviations.

## RQ9 Data and Answer (`data/outputs/rq9`)

### `rq9_team_age_vs_efficiency.csv`

- Meaning: team-level season aggregation for age vs efficiency.
- Current size: `18` rows (all Bundesliga teams in 2024/25).
- Key columns:
  - `avg_age` (team average age)
  - `goals_per_shot` (efficiency)
  - `total_goals`, `total_shots`, `matches`

### `rq9_team_match_efficiency.csv`

- Meaning: match-level table (`season x game_id x team`) for distribution/variance analysis.
- Current size: `612` rows (`18 teams x 34 matches`).
- Key columns: `avg_age`, `goals`, `shots`, `goals_per_shot`, `home_away`.

### `rq9_optimal_age_summary.csv`

- Meaning: statistical model summary (Pearson correlation + quadratic peak estimate).
- Current result:
  - `pearson_r_age_efficiency = -0.56999`
  - no in-range quadratic optimum (`model_note`: maximum outside observed age range `24.25-27.86`)

### `rq9_player_age_profile.csv` and `rq9_player_best_age.csv`

- Meaning: player-level efficiency grouped by age bands.
- Current result (`min_total_shots=80`): best age band is `33` years with `0.175` goals per shot (`31/177`, `11` players).

### Answer to RQ9 (2024/25)

- Team-level relationship is negative: older squads tend to have lower shooting efficiency in this dataset (`r ~ -0.57`).
- High-efficiency teams are mostly younger/mid-age squads:
  - `Bayern Munich` (`avg_age 25.75`, `goals_per_shot 0.153`)
  - `Borussia Dortmund` (`25.17`, `0.147`)
  - `Bayer Leverkusen` (`25.42`, `0.143`)
- Low-efficiency side includes older teams:
  - `1. FC Union Berlin` (`27.86`, `0.084`)
  - `VfL Bochum` (`27.46`, `0.076`)
- No stable single "optimal team age" can be inferred from the quadratic fit for 2024/25.

Conclusion: RQ9 is answered as a negative association between team average age and goals-per-shot efficiency for Bundesliga 2024/25, without evidence for one robust optimal team age point.

## Notes

- Results depend on data source completeness and current cache contents.
- If you change logic or want fresh data, run with `--refresh`.

