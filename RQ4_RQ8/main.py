"""Run the source pipelines and write all CSV outputs.

Input: optional command line arguments.
Output: raw source CSV files, derived analysis CSV files, and terminal output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from espn_data_download_pipeline import build_espn_dataset
from pipeline_config import build_config, configure_env, parse_args
from pipeline_utils import round_numeric_columns
from rq4_analysis import RQ4_RATINGS_FILE, build_rq4_answer, build_rq4_tables
from rq8_analysis import (
    OPTIMAL_AGE_FILE,
    PLAYER_BEST_AGE_FILE,
    TEAM_EFFICIENCY_FILE,
    build_rq8_answer,
    build_rq8_tables,
)
from whoscored_data_download_pipeline import build_whoscored_dataset


ESPN_OUTPUT_NAME = "espn_player_match_data_for_rq8.csv"
WHOSCORED_OUTPUT_NAME = "whoscored_player_match_data_for_rq4.csv"
PIPELINE_ROOT = Path(__file__).resolve().parent
ANALYSIS_OUTPUT_ROOT = PIPELINE_ROOT / "analysis_output"


def write_output(df: pd.DataFrame, path: Path) -> None:
    """Write one DataFrame to CSV.

    Input: DataFrame and output path.
    Output: no direct return value.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def load_existing_output(path: Path, label: str) -> pd.DataFrame | None:
    """Load a cached CSV output when it already exists.

    Input: output path and short source label.
    Output: loaded DataFrame or `None`.
    """
    if not path.exists():
        return None

    print(f"[info] {label}: using existing output at {path.resolve()}")
    return pd.read_csv(path)


def print_report(espn_df: pd.DataFrame, whoscored_df: pd.DataFrame) -> None:
    """Print short previews of the two raw output tables.

    Input: ESPN and WhoScored DataFrames.
    Output: no direct return value.
    """
    print("\n=== ESPN OUTPUT ===")
    if espn_df.empty:
        print("No ESPN rows available.")
    else:
        print(f"Rows: {len(espn_df)}")
        display = round_numeric_columns(espn_df.head(10), ("age",), 3)
        print(display.to_string(index=False))

    print("\n=== WHOSCORED OUTPUT ===")
    if whoscored_df.empty:
        print("No WhoScored rows available.")
    else:
        print(f"Rows: {len(whoscored_df)}")
        display = round_numeric_columns(
            whoscored_df.head(10),
            ("overall_rating",),
            3,
        )
        print(display.to_string(index=False))


def print_analysis_report(paths: list[Path]) -> None:
    """Print the file paths of the derived analysis CSV files.

    Input: list of written file paths.
    Output: no direct return value.
    """
    print("\n[ok] Generated CSV files with analysis data:")
    for path in paths:
        print(f" - {path.resolve()}")


def print_answer_report(answers: dict[str, str]) -> None:
    """Print the short answer strings.

    Input: dictionary with answer text by key.
    Output: no direct return value.
    """
    print("\n=== ANALYSIS DATA POINTS ===")
    for key in ("rq4", "rq8"):
        answer = answers.get(key, "").strip()
        if answer:
            print(answer)


def build_analysis_tables(
    rq8_df: pd.DataFrame,
    rq4_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build all derived analysis tables.

    Input: raw RQ8 and RQ4 DataFrames.
    Output: dictionary from relative CSV path to DataFrame.
    """
    tables: dict[str, pd.DataFrame] = {}
    tables.update(build_rq4_tables(rq4_df))
    tables.update(build_rq8_tables(rq8_df))
    return tables


def write_analysis_outputs(
    tables: dict[str, pd.DataFrame],
    output_root: Path = ANALYSIS_OUTPUT_ROOT,
) -> list[Path]:
    """Write all derived analysis tables to disk.

    Input: table dictionary and output root path.
    Output: list of written file paths.
    """
    written_paths: list[Path] = []
    for relative_path, df in tables.items():
        path = output_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        written_paths.append(path)
    return written_paths


def build_terminal_answers(
    tables: dict[str, pd.DataFrame],
) -> dict[str, str]:
    """Build short answer strings for the terminal output.

    Input: dictionary with derived analysis tables.
    Output: dictionary with short text answers for RQ4 and RQ8.
    """
    return {
        "rq4": build_rq4_answer(tables[RQ4_RATINGS_FILE]),
        "rq8": build_rq8_answer(
            tables[TEAM_EFFICIENCY_FILE],
            tables[PLAYER_BEST_AGE_FILE],
            tables[OPTIMAL_AGE_FILE],
        ),
    }


def main(argv: Iterable[str] | None = None) -> int:
    """Run the full pipeline and save all output files.

    Input: optional iterable of CLI argument strings.
    Output: process exit code.
    """
    args = parse_args(argv)
    config = build_config(args)
    configure_env(config)
    espn_path = config.output_dir / ESPN_OUTPUT_NAME
    whoscored_path = config.output_dir / WHOSCORED_OUTPUT_NAME

    try:
        if config.refresh:
            espn_df = build_espn_dataset(config)
            whoscored_df = build_whoscored_dataset(config)
        else:
            espn_df = load_existing_output(espn_path, "ESPN")
            if espn_df is None:
                espn_df = build_espn_dataset(config)

            whoscored_df = load_existing_output(whoscored_path, "WhoScored")
            if whoscored_df is None:
                whoscored_df = build_whoscored_dataset(config)
    except Exception as exc:
        print(f"[error] Pipeline failed: {exc}")
        return 1

    try:
        write_output(espn_df, espn_path)
        write_output(whoscored_df, whoscored_path)
        analysis_tables = build_analysis_tables(espn_df, whoscored_df)
        analysis_paths = write_analysis_outputs(analysis_tables)
        answers = build_terminal_answers(analysis_tables)
    except Exception as exc:
        print(f"[error] Failed to save outputs: {exc}")
        return 1

    print_report(espn_df, whoscored_df)
    print("\n[ok] Saved:")
    print(f" - {espn_path.resolve()}")
    print(f" - {whoscored_path.resolve()}")
    print_analysis_report(analysis_paths)
    print_answer_report(answers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
