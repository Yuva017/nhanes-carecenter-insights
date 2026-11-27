"""Run the CareCenter SQL checks on a disposable PostgreSQL database."""

import argparse

from src.database_validation import run_database_validation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, help="Name of the validation database")
    args = parser.parse_args()

    try:
        return run_database_validation(args.database)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
