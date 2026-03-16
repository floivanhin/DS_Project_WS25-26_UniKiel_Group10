"""Build the derived analysis tables for RQ8.

Input: raw ESPN output data.
Output: derived RQ8 tables and short terminal answer text.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


BEST_AGE_MIN_TOTAL_SHOTS = 80
SEASON_SUMMARY_FILE = "rq8/bundesliga_season_age_summary.csv"
TEAM_SUMMARY_FILE = "rq8/bundesliga_team_age_summary.csv"
TEAM_MATCH_FILE = "rq8/rq8_team_match_efficiency.csv"
TEAM_EFFICIENCY_FILE = "rq8/rq8_team_age_vs_efficiency.csv"
PLAYER_AGE_PROFILE_FILE = "rq8/rq8_player_age_profile.csv"
PLAYER_BEST_AGE_FILE = "rq8/rq8_player_best_age.csv"
OPTIMAL_AGE_FILE = "rq8/rq8_optimal_age_summary.csv"


def first_non_null(series: pd.Series) -> object:
    """Return the first non-null value from a Series.

    Input: pandas Series.
    Output: first non-null value or `nan`.
    """
    valid = series.dropna()
    if valid.empty:
        return np.nan
    return valid.iloc[0]


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide two Series and keep `nan` for zero denominators.

    Input: numerator Series and denominator Series.
    Output: float Series with safe division.
    """
    top = pd.to_numeric(numerator, errors="coerce")
    bottom = pd.to_numeric(denominator, errors="coerce")
    return top.divide(bottom.where(bottom != 0))


def fit_correlation(x: pd.Series, y: pd.Series) -> float:
    """Return the Pearson correlation for two numeric Series.

    Input: two pandas Series.
    Output: float correlation or `nan`.
    """
    valid = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(valid) < 2:
        return float("nan")
    return float(valid["x"].corr(valid["y"]))


def normalize_rq8(rq8_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the raw ESPN table for downstream analysis.

    Input: raw RQ8 DataFrame.
    Output: copied DataFrame with cleaned types.
    """
    out = rq8_df.copy()
    out["season"] = out["season"].astype(str)
    out["game_id"] = out["game_id"].astype(str)
    out["player_id"] = out["player_id"].astype(str)
    for column in (
        "age",
        "player_goals",
        "player_shots",
        "team_goals",
        "team_shots",
    ):
        out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def build_season_age_summary(rq8_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate one age summary row per season.

    Input: normalized RQ8 DataFrame.
    Output: DataFrame for `rq8/bundesliga_season_age_summary.csv`.
    """
    season_players = (
        rq8_df.groupby(["season", "season_label", "player_id"], dropna=False)
        .agg(age=("age", first_non_null))
        .reset_index()
    )
    return (
        season_players.groupby(["season", "season_label"], dropna=False)
        .agg(
            unique_players=("player_id", "nunique"),
            avg_age=("age", "mean"),
            min_age=("age", "min"),
            max_age=("age", "max"),
            missing_age=("age", lambda series: int(series.isna().sum())),
        )
        .reset_index()
        .sort_values(["season"], kind="stable")
    )


def build_team_age_summary(rq8_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate one age summary row per team.

    Input: normalized RQ8 DataFrame.
    Output: DataFrame for `rq8/bundesliga_team_age_summary.csv`.
    """
    team_players = (
        rq8_df.groupby(
            ["season", "season_label", "team", "player_id"],
            dropna=False,
        )
        .agg(age=("age", first_non_null))
        .reset_index()
    )
    return (
        team_players.groupby(
            ["season", "season_label", "team"],
            dropna=False,
        )
        .agg(
            player_count=("player_id", "nunique"),
            avg_age=("age", "mean"),
            min_age=("age", "min"),
            max_age=("age", "max"),
            missing_age=("age", lambda series: int(series.isna().sum())),
        )
        .reset_index()
        .sort_values(
            ["season", "avg_age", "team"],
            ascending=[True, False, True],
            kind="stable",
        )
    )


def build_team_match_efficiency(
    rq8_df: pd.DataFrame,
    team_age_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build one team-match row with goals, shots, and average age.

    Input: normalized RQ8 DataFrame and team age summary DataFrame.
    Output: DataFrame for `rq8_team_match_efficiency.csv`.
    """
    team_lookup = team_age_df[
        ["season", "season_label", "team", "avg_age"]
    ].drop_duplicates()
    match_df = (
        rq8_df.groupby(
            ["season", "season_label", "game_id", "team"],
            dropna=False,
        )
        .agg(
            goals=("team_goals", first_non_null),
            shots=("team_shots", first_non_null),
        )
        .reset_index()
        .merge(
            team_lookup,
            how="left",
            on=["season", "season_label", "team"],
        )
    )
    match_df["goals_per_shot"] = safe_ratio(
        match_df["goals"],
        match_df["shots"],
    )
    return match_df[
        [
            "season",
            "season_label",
            "game_id",
            "team",
            "avg_age",
            "goals",
            "shots",
            "goals_per_shot",
        ]
    ].sort_values(["season", "game_id", "team"], kind="stable")


def build_team_age_vs_efficiency(team_match_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate team efficiency against average age.

    Input: team-match DataFrame.
    Output: DataFrame for `rq8_team_age_vs_efficiency.csv`.
    """
    team_df = (
        team_match_df.groupby(
            ["season", "season_label", "team", "avg_age"],
            dropna=False,
        )
        .agg(
            matches=("game_id", "nunique"),
            total_goals=("goals", "sum"),
            total_shots=("shots", "sum"),
        )
        .reset_index()
    )
    team_df["goals_per_shot"] = safe_ratio(
        team_df["total_goals"],
        team_df["total_shots"],
    )
    return team_df[
        [
            "season",
            "season_label",
            "team",
            "avg_age",
            "matches",
            "total_goals",
            "total_shots",
            "goals_per_shot",
        ]
    ].sort_values(
        ["season", "goals_per_shot", "team"],
        ascending=[True, False, True],
        kind="stable",
    )


def build_player_age_profile(rq8_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate player efficiency by integer age band.

    Input: normalized RQ8 DataFrame.
    Output: DataFrame for `rq8_player_age_profile.csv`.
    """
    working = rq8_df.dropna(subset=["age"]).copy()
    working["age_int"] = np.floor(working["age"]).astype(int)
    profile = (
        working.groupby(["season", "age_int"], dropna=False)
        .agg(
            players=("player_id", "nunique"),
            total_goals=("player_goals", "sum"),
            total_shots=("player_shots", "sum"),
        )
        .reset_index()
    )
    profile = profile.loc[profile["total_shots"] > 0].copy()
    profile["goals_per_shot"] = safe_ratio(
        profile["total_goals"],
        profile["total_shots"],
    )
    return profile.sort_values(
        ["season", "goals_per_shot", "total_shots", "age_int"],
        ascending=[True, False, False, True],
        kind="stable",
    )


def build_best_age_candidate(
    profile: pd.DataFrame,
    season: str,
) -> pd.DataFrame:
    """Pick the best eligible player age band for one season scope.

    Input: age profile DataFrame and season label.
    Output: one-row DataFrame or empty DataFrame.
    """
    eligible = profile.loc[
        profile["total_shots"] >= BEST_AGE_MIN_TOTAL_SHOTS
    ].copy()
    if eligible.empty:
        return pd.DataFrame(
            columns=[
                "season",
                "min_total_shots",
                "best_age_int",
                "goals_per_shot",
                "total_shots",
                "total_goals",
                "players",
            ]
        )

    best_row = (
        eligible.sort_values(
            ["goals_per_shot", "total_shots", "total_goals", "age_int"],
            ascending=[False, False, False, True],
            kind="stable",
        )
        .head(1)
        .copy()
    )
    if "season" in best_row.columns:
        best_row["season"] = season
    else:
        best_row.insert(0, "season", season)

    best_row.insert(1, "min_total_shots", BEST_AGE_MIN_TOTAL_SHOTS)
    best_row = best_row.rename(columns={"age_int": "best_age_int"})
    return best_row[
        [
            "season",
            "min_total_shots",
            "best_age_int",
            "goals_per_shot",
            "total_shots",
            "total_goals",
            "players",
        ]
    ]


def build_player_best_age(rq8_df: pd.DataFrame) -> pd.DataFrame:
    """Compute the strongest player age band per season.

    Input: normalized RQ8 DataFrame.
    Output: DataFrame for `rq8_player_best_age.csv`.
    """
    rows = []
    per_season_profile = build_player_age_profile(rq8_df)
    for season, group in per_season_profile.groupby("season", sort=True):
        rows.append(build_best_age_candidate(group.copy(), str(season)))
    return pd.concat(rows, ignore_index=True)


def build_quadratic_model_row(
    season: str,
    team_df: pd.DataFrame,
) -> dict[str, object]:
    """Fit one quadratic age-efficiency model summary row.

    Input: season label and team summary DataFrame.
    Output: dictionary with model summary values.
    """
    valid = team_df.dropna(subset=["avg_age", "goals_per_shot"]).copy()
    if valid.empty:
        return {
            "season": season,
            "n_teams": 0,
            "pearson_r_age_efficiency": np.nan,
            "estimated_peak_age": np.nan,
            "estimated_peak_goals_per_shot": np.nan,
            "model_note": "No valid team rows were available.",
        }

    pearson = fit_correlation(valid["avg_age"], valid["goals_per_shot"])
    min_age = float(valid["avg_age"].min())
    max_age = float(valid["avg_age"].max())

    if len(valid) < 3:
        return {
            "season": season,
            "n_teams": int(len(valid)),
            "pearson_r_age_efficiency": pearson,
            "estimated_peak_age": np.nan,
            "estimated_peak_goals_per_shot": np.nan,
            "model_note": "Not enough rows for a quadratic model.",
        }

    quad_a, quad_b, quad_c = np.polyfit(
        valid["avg_age"],
        valid["goals_per_shot"],
        2,
    )
    if quad_a >= 0:
        return {
            "season": season,
            "n_teams": int(len(valid)),
            "pearson_r_age_efficiency": pearson,
            "estimated_peak_age": np.nan,
            "estimated_peak_goals_per_shot": np.nan,
            "model_note": "Quadratic model has no concave maximum.",
        }

    peak_age = -quad_b / (2 * quad_a)
    peak_efficiency = quad_a * peak_age**2 + quad_b * peak_age + quad_c
    if peak_age < min_age or peak_age > max_age:
        note = (
            "The fitted quadratic peak lies outside the observed "
            "team-average age range "
            f"({min_age:.2f}-{max_age:.2f}), so the data does not support "
            "one exact optimal team-average age."
        )
        return {
            "season": season,
            "n_teams": int(len(valid)),
            "pearson_r_age_efficiency": pearson,
            "estimated_peak_age": float(peak_age),
            "estimated_peak_goals_per_shot": float(peak_efficiency),
            "model_note": note,
        }

    return {
        "season": season,
        "n_teams": int(len(valid)),
        "pearson_r_age_efficiency": pearson,
        "estimated_peak_age": float(peak_age),
        "estimated_peak_goals_per_shot": float(peak_efficiency),
        "model_note": "",
    }


def build_optimal_age_summary(team_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize RQ8 age-efficiency model results by season.

    Input: team summary DataFrame.
    Output: DataFrame for `rq8_optimal_age_summary.csv`.
    """
    rows = []
    for season, group in team_df.groupby("season", sort=True):
        rows.append(
            build_quadratic_model_row(
                str(season),
                group.copy(),
            )
        )
    return pd.DataFrame.from_records(rows)


def build_rq8_tables(rq8_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build all derived RQ8 tables.

    Input: raw RQ8 DataFrame.
    Output: dictionary from relative CSV path to DataFrame.
    """
    normalized = normalize_rq8(rq8_df)
    season_age = build_season_age_summary(normalized)
    team_age = build_team_age_summary(normalized)
    team_match = build_team_match_efficiency(normalized, team_age)
    team_efficiency = build_team_age_vs_efficiency(team_match)
    age_profile = build_player_age_profile(normalized)
    best_age = build_player_best_age(normalized)
    optimal_age = build_optimal_age_summary(team_efficiency)
    return {
        SEASON_SUMMARY_FILE: season_age,
        TEAM_SUMMARY_FILE: team_age,
        TEAM_MATCH_FILE: team_match,
        TEAM_EFFICIENCY_FILE: team_efficiency,
        PLAYER_AGE_PROFILE_FILE: age_profile,
        PLAYER_BEST_AGE_FILE: best_age,
        OPTIMAL_AGE_FILE: optimal_age,
    }


def build_rq8_answer(
    team_df: pd.DataFrame,
    best_age_df: pd.DataFrame,
    optimal_df: pd.DataFrame,
) -> str:
    """Build the short RQ8 answer string for the terminal output.

    Input: team summary, best-age summary, and model summary DataFrames.
    Output: formatted answer string.
    """
    best_age_row = best_age_df.loc[best_age_df["season"] != "all"].head(1)
    if best_age_row.empty:
        best_age_row = best_age_df.head(1)

    optimal_row = optimal_df.head(1)
    if optimal_row.empty:
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
