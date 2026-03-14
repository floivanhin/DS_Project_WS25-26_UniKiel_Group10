"""Load the datasets required by the RQ9 Dash page.

Input: local RQ9 diagram tables and shared downloaded source table data.
Output: a cached `RQ9Data` object with pandas DataFrames for RQ9.
"""

import dataclasses
import functools
import pathlib

import pandas as pd


@dataclasses.dataclass(frozen=True)
class RQ9Data:
    """Store the DataFrames required by the RQ9 page.

    Input: loaded pandas DataFrames for the RQ9 analysis.
    Output: immutable grouped access to the RQ9 datasets.
    """

    season_age_summary: pd.DataFrame
    team_age_summary: pd.DataFrame
    team_match_efficiency: pd.DataFrame
    team_age_efficiency: pd.DataFrame
    optimal_age_summary: pd.DataFrame
    espn_player_match_data: pd.DataFrame


def _read_csv(csv_path):
    """Read one RQ9 CSV file and fail clearly if it is missing."""

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Required RQ9 dataset is missing: {csv_path}"
        )
    return pd.read_csv(csv_path)


@functools.lru_cache(maxsize=1)
def load_rq9_data():
    """Return the cached CSV datasets for the RQ9 page.

    Input: no arguments; paths are resolved relative to this module.
    Output: `RQ9Data` with all required DataFrames loaded.
    """

    rq_root = pathlib.Path(__file__).resolve().parent
    rq4_rq9_root = rq_root.parent

    return RQ9Data(
        season_age_summary=_read_csv(
            rq_root
            / "analysis_diagram_data"
            / "bundesliga_season_age_summary.csv"
        ),
        team_age_summary=_read_csv(
            rq_root
            / "analysis_diagram_data"
            / "bundesliga_team_age_summary.csv"
        ),
        team_match_efficiency=_read_csv(
            rq_root
            / "analysis_diagram_data"
            / "rq9_team_match_efficiency.csv"
        ),
        team_age_efficiency=_read_csv(
            rq_root
            / "analysis_diagram_data"
            / "rq9_team_age_vs_efficiency.csv"
        ),
        optimal_age_summary=_read_csv(
            rq_root
            / "analysis_diagram_data"
            / "rq9_optimal_age_summary.csv"
        ),
        espn_player_match_data=_read_csv(
            rq4_rq9_root
            / "data"
            / "downloaded_outputs_to_analyse"
            / "espn_player_match_data_for_rq9.csv"
        ),
    )
