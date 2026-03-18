import pandas as pd


RQ4_MIN_MATCHES_FOR_LEADERBOARD = 5
RQ4_MIN_MATCHES_PER_SIDE_FOR_DELTA = 5
RQ4_RATINGS_FILE = "rq4/rq4_home_away_player_ratings.csv"
RQ4_DELTA_FILE = "rq4/rq4_player_home_away_delta.csv"

# columns for the main rq4 table
RATINGS_COLUMNS = [
    "season",
    "season_label",
    "home_away",
    "player",
    "player_id",
    "matches",
    "teams",
    "avg_overall_rating",
    "median_overall_rating",
    "best_overall_rating",
    "worst_overall_rating",
    "starts",
    "motm_awards",
    "eligible_for_leaderboard",
]

# columns for the home vs away diff table
DELTA_COLUMNS = [
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


# turn weird truthy stuff into bool
def boolish(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


# make the rq4 csv tables
def rq4_tables(rq4_df):
    if rq4_df.empty:
        return {
            RQ4_RATINGS_FILE: pd.DataFrame(columns=RATINGS_COLUMNS),
            RQ4_DELTA_FILE: pd.DataFrame(columns=DELTA_COLUMNS),
        }

    # clean the raw columns a bit
    df = rq4_df.copy()
    df["season"] = df["season"].astype(str)
    df["game_id"] = df["game_id"].astype(str)
    df["player_id"] = df["player_id"].astype(str)
    df["overall_rating"] = pd.to_numeric(df["overall_rating"], errors="coerce")
    df["is_starting_xi"] = df["is_starting_xi"].map(boolish)
    df["is_man_of_the_match"] = df["is_man_of_the_match"].map(boolish)

    # main table by player and side
    ratings = (
        df.groupby(
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
    ratings["eligible_for_leaderboard"] = (
        ratings["matches"] >= RQ4_MIN_MATCHES_FOR_LEADERBOARD
    )
    ratings = ratings[RATINGS_COLUMNS].sort_values(
        ["season", "home_away", "avg_overall_rating", "matches", "player"],
        ascending=[True, True, False, False, True],
        kind="stable",
    )

    # split home and away so we can compare them
    home = ratings.loc[ratings["home_away"] == "home"].copy()
    away = ratings.loc[ratings["home_away"] == "away"].copy()

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

    # join both sides into one row
    delta = home.merge(
        away,
        how="inner",
        on=["season", "season_label", "player", "player_id"],
    )
    if delta.empty:
        delta = pd.DataFrame(columns=DELTA_COLUMNS)
    else:
        # simple difference stuff
        delta["matches_total"] = delta["home_matches"] + delta["away_matches"]
        delta["avg_rating_delta_home_minus_away"] = (
            delta["home_avg_overall_rating"] - delta["away_avg_overall_rating"]
        )
        delta["abs_avg_rating_delta"] = (
            delta["avg_rating_delta_home_minus_away"].abs()
        )
        delta["eligible_both_sides"] = (
            delta["home_matches"] >= RQ4_MIN_MATCHES_PER_SIDE_FOR_DELTA
        ) & (delta["away_matches"] >= RQ4_MIN_MATCHES_PER_SIDE_FOR_DELTA)
        delta = delta[DELTA_COLUMNS].sort_values(
            [
                "season",
                "abs_avg_rating_delta",
                "avg_rating_delta_home_minus_away",
                "player",
            ],
            ascending=[True, False, False, True],
            kind="stable",
        )

    return {
        RQ4_RATINGS_FILE: ratings.reset_index(drop=True),
        RQ4_DELTA_FILE: delta.reset_index(drop=True),
    }


# build the short text answer
def rq4_answer(ratings_df):
    home = ratings_df.loc[
        ratings_df["eligible_for_leaderboard"]
        & (ratings_df["home_away"] == "home"),
        "avg_overall_rating",
    ]
    away = ratings_df.loc[
        ratings_df["eligible_for_leaderboard"]
        & (ratings_df["home_away"] == "away"),
        "avg_overall_rating",
    ]

    mean_home = float(home.mean()) if not home.empty else float("nan")
    mean_away = float(away.mean()) if not away.empty else float("nan")

    # just grab the first ranked player
    top_home = ratings_df.loc[
        ratings_df["eligible_for_leaderboard"]
        & (ratings_df["home_away"] == "home")
    ].head(1)
    top_away = ratings_df.loc[
        ratings_df["eligible_for_leaderboard"]
        & (ratings_df["home_away"] == "away")
    ].head(1)

    top_home_player = str(top_home.iloc[0]["player"]) if not top_home.empty else "n/a"
    top_away_player = str(top_away.iloc[0]["player"]) if not top_away.empty else "n/a"

    return (
        "RQ4 | "
        f"top_home={top_home_player} | "
        f"top_away={top_away_player} | "
        f"mean_home={mean_home:.3f} | "
        f"mean_away={mean_away:.3f} | "
        f"delta={mean_home - mean_away:+.3f}"
    )
