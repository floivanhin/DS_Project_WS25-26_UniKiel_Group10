"""Configuration helpers for the Bundesliga data pipeline.

Input: command line arguments.
Output: validated pipeline configuration values.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pipeline_utils import DEFAULT_LEAGUE, TARGET_SEASON


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "downloaded_outputs_to_analyse"


@dataclass(frozen=True)
class Config:
    """Store the pipeline configuration in one small object.

    Input: league, season, output directory, and refresh flag.
    Output: immutable configuration object.
    """

    league: str
    season: str
    output_dir: Path
    refresh: bool


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the pipeline.

    Input: optional iterable of argument strings.
    Output: argparse namespace with raw argument values.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Build Bundesliga player-level source datasets "
            "from ESPN and WhoScored."
        )
    )
    parser.add_argument("--league", default=DEFAULT_LEAGUE)
    parser.add_argument("--season", default=TARGET_SEASON)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument("--refresh", action="store_true")
    return parser.parse_args(list(argv) if argv is not None else None)


def build_config(args: argparse.Namespace) -> Config:
    """Convert raw CLI arguments into a cleaned Config object.

    Input: argparse namespace.
    Output: Config instance with normalized values.
    """
    season = str(args.season).strip()
    league = str(args.league).strip()
    return Config(
        league=league or DEFAULT_LEAGUE,
        season=season or TARGET_SEASON,
        output_dir=Path(args.output_dir).resolve(),
        refresh=bool(args.refresh),
    )


def configure_env(config: Config) -> None:
    """Prepare the output directory and common environment settings.

    Input: Config instance.
    Output: no direct return value.
    """
    config.output_dir.mkdir(parents=True, exist_ok=True)
    os.environ["SOCCERDATA_LOGLEVEL"] = "WARNING"
