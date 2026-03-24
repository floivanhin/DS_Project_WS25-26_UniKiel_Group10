import os
from pathlib import Path

import pandas as pd

from espn_data_download_pipeline import build_espn_dataset
from rq4_analysis import RQ4_RATINGS_FILE, rq4_answer, rq4_tables
from rq8_analysis import (
    OPTIMAL_AGE_FILE,
    PLAYER_BEST_AGE_FILE,
    TEAM_EFFICIENCY_FILE,
    rq8_answer,
    rq8_tables,
)
from whoscored_data_download_pipeline import build_whoscored_dataset

ESPN_OUTPUT_NAME = "espn_player_match_data_for_rq8.csv"
WHOSCORED_OUTPUT_NAME = "whoscored_player_match_data_for_rq4.csv"

# Default Configuration of Bundesliga 24/25
LEAGUE = "GER-Bundesliga"
SEASON = "2425"
REFRESH = False
OUTPUT_DIR = (
    Path(__file__).resolve().parent
    / "data"
    / "downloaded_outputs_to_analyse"
)
ANALYSIS_DIR = Path(__file__).resolve().parent / "analysis_output"

def main():
    # basic setup what data should be fetched
    league = LEAGUE
    season = SEASON
    refresh = REFRESH
    output_dir = OUTPUT_DIR.resolve()

    # create directory if not exists
    output_dir.mkdir(parents=True, exist_ok=True)

    os.environ["SOCCERDATA_LOGLEVEL"] = "WARNING"

    espn_path = output_dir / ESPN_OUTPUT_NAME
    whoscored_path = output_dir / WHOSCORED_OUTPUT_NAME

    # use old file if we have it
    if not refresh and espn_path.exists():
        print("use saved ESPN csv")
        espn_df = pd.read_csv(espn_path)
    else:
        print("load ESPN data")
        espn_df = build_espn_dataset(league, season, refresh)

    # same idea here
    if not refresh and whoscored_path.exists():
        print("use saved WhoScored csv")
        whoscored_df = pd.read_csv(whoscored_path)
    else:
        print("load WhoScored data")
        whoscored_df = build_whoscored_dataset(league, season, refresh)

    # save raw data
    espn_df.to_csv(espn_path, index=False)
    whoscored_df.to_csv(whoscored_path, index=False)

    # build the answer tables
    print("run rq4")
    rq4 = rq4_tables(whoscored_df)
    print("run rq8")
    rq8 = rq8_tables(espn_df)

    # save all analysis csvs
    for name, df in {**rq4, **rq8}.items():
        path = ANALYSIS_DIR / name
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        print(f"saved {path.name}")

    # quick output
    print(f"saved {espn_path.resolve()}")
    print(f"saved {whoscored_path.resolve()}")
    print(rq4_answer(rq4[RQ4_RATINGS_FILE]))
    print(
        rq8_answer(
            rq8[TEAM_EFFICIENCY_FILE],
            rq8[PLAYER_BEST_AGE_FILE],
            rq8[OPTIMAL_AGE_FILE],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
