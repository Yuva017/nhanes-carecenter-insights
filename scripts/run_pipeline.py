"""Orchestrator: extract -> transform -> stage -> load."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import load_config
from jobs.load import run_pipeline


def main() -> None:
    run_pipeline(load_config())


if __name__ == "__main__":
    main()
