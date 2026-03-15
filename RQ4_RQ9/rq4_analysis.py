"""Build the derived analysis tables for RQ4.

Input: raw WhoScored output data.
Output: derived RQ4 tables and short terminal answer text.
"""

from __future__ import annotations

import pandas as pd


RQ4_MIN_MATCHES_FOR_LEADERBOARD = 5
RQ4_MIN_MATCHES_PER_SIDE_FOR_DELTA = 5
RQ4_RATINGS_FILE = "rq4/rq4_home_away_player_ratings.csv"
RQ4_DELTA_FILE = "rq4/rq4_player_home_away_delta.csv"


def is_true(value: object) -> bool:
    """Convert loose truthy values into a boolean.

    Input: raw boolean-like value.
    Output: `True` or `False`.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def normalize_rq4(rq4_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the raw WhoScored table for downstream analysis.

    Input: raw RQ4 DataFrame.
    Output: copied DataFrame with cleaned types.
    """
    out = rq4_df.copy()
    out["season"] = out["season"].astype(str)
    out["game_id"] = out["game_id"].astype(str)
    out["player_id"] = out["player_id"].astype(str)
    out["overall_rating"] = pd.to_numeric(
        out["overall_rating"],
        errors="coerce",
    )
    out["is_starting_xi"] = out["is_starting_xi"].map(is_true)
    out["is_man_of_the_match"] = out["is_man_of_the_match"].map(is_true)
    return out


def build_rq4_home_away_player_ratings(rq4_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate player ratings by home and away matches.

    Input: normalized RQ4 DataFrame.
    Output: DataFrame for `rq4_home_away_player_ratings.csv`.
    """
    summary = (
        rq4_df.groupby(
            ["season", "season_label", "home_away", "player", "player_id"],
            dropna=False,
        )
        .agg(
            matches=("game_id", "nunique"),
            teams=("team", "nunique"),
            avg_overall_rating=("overall_rating", "mean"),
            median_overall_rating=("overall_rating", "median"),
            best_overall_rating=("overall_rating", "max"),
            worst_overall_rating=("overall_rating", "min"),
            starts=("is_starting_xi", "sum"),
            motm_awards=("is_man_of_the_match", "sum"),
        )
        .reset_index()
    )
    summary["eligible_for_leaderboard"] = (
        summary["matches"] >= RQ4_MIN_MATCHES_FOR_LEADERBOARD
    )
    return summary.sort_values(
        ["season", "home_away", "avg_overall_rating", "matches", "player"],
        ascending=[True, True, False, False, True],
        kind="stable",
    )


def build_rq4_player_home_away_delta(ratings_df: pd.DataFrame) -> pd.DataFrame:
    """Compare average player ratings between home and away matches.

    Input: aggregated RQ4 ratings DataFrame.
    Output: DataFrame for `rq4_player_home_away_delta.csv`.
    """
    join_keys = ["season", "season_label", "player", "player_id"]
    value_columns = [
        "matches",
        "teams",
        "avg_overall_rating",
        "median_overall_rating",
        "best_overall_rating",
        "worst_overall_rating",
        "starts",
        "motm_awards",
    ]

    home = ratings_df.loc[
        ratings_df["home_away"] == "home",
        join_keys + value_columns,
    ].copy()
    away = ratings_df.loc[
        ratings_df["home_away"] == "away",
        join_keys + value_columns,
    ].copy()

    home = home.rename(
        columns={
            "matches": "home_matches",
            "teams": "home_teams",
            "avg_overall_rating": "home_avg_overall_rating",
            "median_overall_rating": "home_median_overall_rating",
            "best_overall_rating": "home_best_overall_rating",
            "worst_overall_rating": "home_worst_overall_rating",
            "starts": "home_starts",
            "motm_awards": "home_motm_awards",
        }
    )
    away = away.rename(
        columns={
            "matches": "away_matches",
            "teams": "away_teams",
            "avg_overall_rating": "away_avg_overall_rating",
            "median_overall_rating": "away_median_overall_rating",
            "best_overall_rating": "away_best_overall_rating",
            "worst_overall_rating": "away_worst_overall_rating",
            "starts": "away_starts",
            "motm_awards": "away_motm_awards",
        }
    )

    delta = home.merge(away, how="inner", on=join_keys)
    delta["matches_total"] = delta["home_matches"] + delta["away_matches"]
    delta["avg_rating_delta_home_minus_away"] = (
        delta["home_avg_overall_rating"]
        - delta["away_avg_overall_rating"]
    )
    delta["abs_avg_rating_delta"] = (
        delta["avg_rating_delta_home_minus_away"].abs()
    )
    delta["eligible_both_sides"] = (
        delta["home_matches"] >= RQ4_MIN_MATCHES_PER_SIDE_FOR_DELTA
    ) & (
        delta["away_matches"] >= RQ4_MIN_MATCHES_PER_SIDE_FOR_DELTA
    )

    return delta[
        [
            "season",
            "season_label",
            "player",
            "player_id",
            "home_matches",
            "away_matches",
            "matches_total",
            "home_avg_overall_rating",
            "away_avg_overall_rating",
            "avg_rating_delta_home_minus_away",
            "abs_avg_rating_delta",
            "home_median_overall_rating",
            "away_median_overall_rating",
            "home_best_overall_rating",
            "away_best_overall_rating",
            "home_worst_overall_rating",
            "away_worst_overall_rating",
            "home_starts",
            "away_starts",
            "home_motm_awards",
            "away_motm_awards",
            "home_teams",
            "away_teams",
            "eligible_both_sides",
        ]
    ].sort_values(
        [
            "season",
            "abs_avg_rating_delta",
            "avg_rating_delta_home_minus_away",
            "player",
        ],
        ascending=[True, False, False, True],
        kind="stable",
    )


def build_rq4_tables(rq4_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build all derived RQ4 tables.

    Input: raw RQ4 DataFrame.
    Output: dictionary from relative CSV path to DataFrame.
    """
    normalized = normalize_rq4(rq4_df)
    ratings = build_rq4_home_away_player_ratings(normalized)
    delta = build_rq4_player_home_away_delta(ratings)
    return {
        RQ4_RATINGS_FILE: ratings,
        RQ4_DELTA_FILE: delta,
    }


def build_rq4_answer(ratings_df: pd.DataFrame) -> str:
    """Build the short RQ4 answer string for the terminal output.

    Input: RQ4 ratings DataFrame.
    Output: formatted answer string.
    """
    rq4_home = ratings_df.loc[
        ratings_df["eligible_for_leaderboard"]
        & (ratings_df["home_away"] == "home"),
        "avg_overall_rating",
    ]
    rq4_away = ratings_df.loc[
        ratings_df["eligible_for_leaderboard"]
        & (ratings_df["home_away"] == "away"),
        "avg_overall_rating",
    ]
    mean_home = float(rq4_home.mean()) if not rq4_home.empty else float("nan")
    mean_away = float(rq4_away.mean()) if not rq4_away.empty else float("nan")
    mean_delta = mean_home - mean_away

    top_home_row = ratings_df.loc[
        ratings_df["eligible_for_leaderboard"]
        & (ratings_df["home_away"] == "home")
    ].head(1)
    top_away_row = ratings_df.loc[
        ratings_df["eligible_for_leaderboard"]
        & (ratings_df["home_away"] == "away")
    ].head(1)

    top_home_player = (
        str(top_home_row.iloc[0]["player"])
        if not top_home_row.empty
        else "n/a"
    )
    top_away_player = (
        str(top_away_row.iloc[0]["player"])
        if not top_away_row.empty
        else "n/a"
    )
    return (
        "RQ4 | "
        f"top_home={top_home_player} | "
        f"top_away={top_away_player} | "
        f"mean_home={mean_home:.3f} | "
        f"mean_away={mean_away:.3f} | "
        f"delta={mean_delta:+.3f}"
    )
