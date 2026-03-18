import numpy as np
import pandas as pd


BEST_AGE_MIN_TOTAL_SHOTS = 80
TEAM_EFFICIENCY_FILE = "rq8/rq8_team_age_vs_efficiency.csv"
PLAYER_AGE_PROFILE_FILE = "rq8/rq8_player_age_profile.csv"
PLAYER_BEST_AGE_FILE = "rq8/rq8_player_best_age.csv"
OPTIMAL_AGE_FILE = "rq8/rq8_optimal_age_summary.csv"

# columns for the team summary table
TEAM_COLUMNS = [
    "season",
    "season_label",
    "team",
    "avg_age",
    "matches",
    "total_goals",
    "total_shots",
    "goals_per_shot",
]

# columns for player age buckets
PROFILE_COLUMNS = [
    "season",
    "age_int",
    "players",
    "total_goals",
    "total_shots",
    "goals_per_shot",
]

# columns for the best age result
BEST_AGE_COLUMNS = [
    "season",
    "min_total_shots",
    "best_age_int",
    "goals_per_shot",
    "total_shots",
    "total_goals",
    "players",
]

# columns for the quadratic model table
OPTIMAL_COLUMNS = [
    "season",
    "n_teams",
    "pearson_r_age_efficiency",
    "estimated_peak_age",
    "estimated_peak_goals_per_shot",
    "model_note",
]


# get one usable value
def first_value(series):
    series = series.dropna()
    if series.empty:
        return np.nan
    return series.iloc[0]


# divide without blowing up on zero
def safe_ratio(top, bottom):
    top = pd.to_numeric(top, errors="coerce")
    bottom = pd.to_numeric(bottom, errors="coerce")
    return top.divide(bottom.where(bottom != 0))


# make the rq8 csv tables
def rq8_tables(rq8_df):
    if rq8_df.empty:
        return {
            TEAM_EFFICIENCY_FILE: pd.DataFrame(columns=TEAM_COLUMNS),
            PLAYER_AGE_PROFILE_FILE: pd.DataFrame(columns=PROFILE_COLUMNS),
            PLAYER_BEST_AGE_FILE: pd.DataFrame(columns=BEST_AGE_COLUMNS),
            OPTIMAL_AGE_FILE: pd.DataFrame(columns=OPTIMAL_COLUMNS),
        }

    # clean numeric columns
    df = rq8_df.copy()
    df["season"] = df["season"].astype(str)
    df["game_id"] = df["game_id"].astype(str)
    df["player_id"] = df["player_id"].astype(str)
    for column in ["age", "player_goals", "player_shots", "team_goals", "team_shots"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # team average age
    team_age = (
        df.groupby(["season", "season_label", "team", "player_id"], dropna=False)
        .agg(age=("age", first_value))
        .reset_index()
        .groupby(["season", "season_label", "team"], dropna=False)
        .agg(avg_age=("age", "mean"))
        .reset_index()
    )

    # team shooting totals
    team_totals = (
        df.groupby(["season", "season_label", "game_id", "team"], dropna=False)
        .agg(goals=("team_goals", first_value), shots=("team_shots", first_value))
        .reset_index()
        .groupby(["season", "season_label", "team"], dropna=False)
        .agg(
            matches=("game_id", "nunique"),
            total_goals=("goals", "sum"),
            total_shots=("shots", "sum"),
        )
        .reset_index()
    )

    # merge age and shooting
    team_df = team_age.merge(
        team_totals,
        how="left",
        on=["season", "season_label", "team"],
    )
    team_df["goals_per_shot"] = safe_ratio(
        team_df["total_goals"],
        team_df["total_shots"],
    )
    team_df = team_df[TEAM_COLUMNS].sort_values(
        ["season", "goals_per_shot", "team"],
        ascending=[True, False, True],
        kind="stable",
    )

    # player age buckets
    profile_df = df.dropna(subset=["age"]).copy()
    if profile_df.empty:
        profile_df = pd.DataFrame(columns=PROFILE_COLUMNS)
    else:
        profile_df["age_int"] = np.floor(profile_df["age"]).astype(int)
        profile_df = (
            profile_df.groupby(["season", "age_int"], dropna=False)
            .agg(
                players=("player_id", "nunique"),
                total_goals=("player_goals", "sum"),
                total_shots=("player_shots", "sum"),
            )
            .reset_index()
        )
        profile_df = profile_df.loc[profile_df["total_shots"] > 0].copy()
        profile_df["goals_per_shot"] = safe_ratio(
            profile_df["total_goals"],
            profile_df["total_shots"],
        )
        profile_df = profile_df[PROFILE_COLUMNS].sort_values(
            ["season", "goals_per_shot", "total_shots", "age_int"],
            ascending=[True, False, False, True],
            kind="stable",
        )

    # best age per season
    best_rows = []
    for season, group in profile_df.groupby("season", sort=True):
        eligible = group.loc[group["total_shots"] >= BEST_AGE_MIN_TOTAL_SHOTS].copy()
        if eligible.empty:
            continue
        best = (
            eligible.sort_values(
                ["goals_per_shot", "total_shots", "total_goals", "age_int"],
                ascending=[False, False, False, True],
                kind="stable",
            )
            .head(1)
            .copy()
        )
        best["season"] = str(season)
        best.insert(1, "min_total_shots", BEST_AGE_MIN_TOTAL_SHOTS)
        best = best.rename(columns={"age_int": "best_age_int"})
        best_rows.append(best[BEST_AGE_COLUMNS])

    if best_rows:
        best_age_df = pd.concat(best_rows, ignore_index=True)
    else:
        best_age_df = pd.DataFrame(columns=BEST_AGE_COLUMNS)

    # simple quadratic summary
    model_rows = []
    for season, group in team_df.groupby("season", sort=True):
        valid = group.dropna(subset=["avg_age", "goals_per_shot"]).copy()
        row = {
            "season": str(season),
            "n_teams": int(len(valid)),
            "pearson_r_age_efficiency": np.nan,
            "estimated_peak_age": np.nan,
            "estimated_peak_goals_per_shot": np.nan,
            "model_note": "",
        }

        if len(valid) >= 2:
            row["pearson_r_age_efficiency"] = float(
                valid["avg_age"].corr(valid["goals_per_shot"])
            )

        if valid.empty:
            row["model_note"] = "No valid team rows were available."
            model_rows.append(row)
            continue

        if len(valid) < 3:
            row["model_note"] = "Not enough rows for a quadratic model."
            model_rows.append(row)
            continue

        quad_a, quad_b, quad_c = np.polyfit(
            valid["avg_age"],
            valid["goals_per_shot"],
            2,
        )

        if quad_a >= 0:
            row["model_note"] = "Quadratic model has no concave maximum."
            model_rows.append(row)
            continue

        peak_age = -quad_b / (2 * quad_a)
        peak_efficiency = quad_a * peak_age**2 + quad_b * peak_age + quad_c
        row["estimated_peak_age"] = float(peak_age)
        row["estimated_peak_goals_per_shot"] = float(peak_efficiency)

        min_age = float(valid["avg_age"].min())
        max_age = float(valid["avg_age"].max())
        if peak_age < min_age or peak_age > max_age:
            row["model_note"] = (
                "The fitted quadratic peak lies outside the observed "
                "team-average age range "
                f"({min_age:.2f}-{max_age:.2f}), so the data does not support "
                "one exact optimal team-average age."
            )

        model_rows.append(row)

    if model_rows:
        optimal_df = pd.DataFrame.from_records(model_rows, columns=OPTIMAL_COLUMNS)
    else:
        optimal_df = pd.DataFrame(columns=OPTIMAL_COLUMNS)

    return {
        TEAM_EFFICIENCY_FILE: team_df.reset_index(drop=True),
        PLAYER_AGE_PROFILE_FILE: profile_df.reset_index(drop=True),
        PLAYER_BEST_AGE_FILE: best_age_df.reset_index(drop=True),
        OPTIMAL_AGE_FILE: optimal_df.reset_index(drop=True),
    }


# build the short text answer
def rq8_answer(team_df, best_age_df, optimal_df):
    # just use the first rows
    best_age_row = best_age_df.head(1)
    optimal_row = optimal_df.head(1)

    pearson = (
        float(optimal_row.iloc[0]["pearson_r_age_efficiency"])
        if not optimal_row.empty
        else np.nan
    )
    best_age_int = (
        int(best_age_row.iloc[0]["best_age_int"])
        if not best_age_row.empty
        else None
    )
    best_age_efficiency = (
        float(best_age_row.iloc[0]["goals_per_shot"])
        if not best_age_row.empty
        else np.nan
    )
    min_team_age = float(team_df["avg_age"].min()) if not team_df.empty else np.nan
    max_team_age = float(team_df["avg_age"].max()) if not team_df.empty else np.nan
    model_note = (
        str(optimal_row.iloc[0]["model_note"]).strip()
        if not optimal_row.empty
        else ""
    )

    answer = (
        "RQ8 | "
        f"pearson={pearson:.3f} | "
        f"team_age_range={min_team_age:.2f}-{max_team_age:.2f} | "
        f"best_player_age_band={best_age_int} | "
        f"band_goals_per_shot={best_age_efficiency:.3f}"
    )
    if model_note and model_note.lower() != "nan":
        answer = f"{answer} | quadratic_peak=outside_range"
    return answer
