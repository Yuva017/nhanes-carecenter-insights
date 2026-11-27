"""Orchestrator: extract -> transform -> stage -> load."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import load_config
from src.jobs.load import run_pipeline
from src.jobs.transform import CYCLE_PERIODS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full",
        action="store_true",
        help="load all supported survey periods without row or participant limits",
    )
    args = parser.parse_args()

    config = load_config()
    pipeline = config["pipeline"]
    if args.full:
        pipeline["cycles"] = list(CYCLE_PERIODS)
        pipeline["max_rows_per_module"] = None
        pipeline["max_participants"] = None

    max_rows = pipeline.get("max_rows_per_module")
    max_participants = pipeline.get("max_participants")
    row_limit = "none" if max_rows is None else f"{max_rows:,} per module"
    participant_limit = "none" if max_participants is None else f"{max_participants:,}"
    cycles = ", ".join(map(str, pipeline["cycles"]))
    print(
        f"Starting NHANES load (source row limit: {row_limit}; "
        f"participant limit: {participant_limit}; survey cycles: {cycles}).",
        flush=True,
    )
    run_pipeline(config)
    print(
        "NHANES load complete. Run python -m scripts.check_counts to verify the database.",
        flush=True,
    )


if __name__ == "__main__":
    main()
