"""Load the datasets required by the RQ4 Dash page.

Input: local RQ4 diagram tables and shared downloaded source table data.
Output: a cached `RQ4Data` object with pandas DataFrames for RQ4.
"""

import dataclasses
import functools
import pathlib

import pandas as pd


@dataclasses.dataclass(frozen=True)
class RQ4Data:
    """Store the DataFrames required by the RQ4 page.

    Input: loaded pandas DataFrames for the RQ4 analysis.
    Output: immutable grouped access to the RQ4 datasets.
    """

    player_ratings: pd.DataFrame
    player_delta: pd.DataFrame
    whoscored_player_match_data: pd.DataFrame


def _read_csv(csv_path):
    """Read one RQ4 CSV file and fail clearly if it is missing."""

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Required RQ4 dataset is missing: {csv_path}"
        )
    return pd.read_csv(csv_path)


def _normalize_bool(series):
    """Turn mixed yes/no values into clean boolean values."""

    return (
        series.fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
    )


@functools.lru_cache(maxsize=1)
def load_rq4_data():
    """Return the cached CSV datasets for the RQ4 page.

    Input: no arguments; paths are resolved relative to this module.
    Output: `RQ4Data` with all required DataFrames loaded.
    """

    rq_root = pathlib.Path(__file__).resolve().parent
    rq4_rq9_root = rq_root.parent

    player_ratings = _read_csv(
        rq_root
        / "analysis_diagram_data"
        / "rq4_home_away_player_ratings.csv"
    )
    player_ratings["eligible_for_leaderboard"] = _normalize_bool(
        player_ratings["eligible_for_leaderboard"]
    )

    player_delta = _read_csv(
        rq_root
        / "analysis_diagram_data"
        / "rq4_player_home_away_delta.csv"
    )
    player_delta["eligible_both_sides"] = _normalize_bool(
        player_delta["eligible_both_sides"]
    )

    whoscored_player_match_data = _read_csv(
        rq4_rq9_root
        / "data"
        / "downloaded_outputs_to_analyse"
        / "whoscored_player_match_data_for_rq4.csv"
    )

    return RQ4Data(
        player_ratings=player_ratings,
        player_delta=player_delta,
        whoscored_player_match_data=whoscored_player_match_data,
    )
