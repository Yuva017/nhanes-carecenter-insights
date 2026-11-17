"""Download the NHANES CSV files used by the ETL from Kaggle."""

import argparse
import shutil
from pathlib import Path

import kagglehub

DATASET = "nguyenvy/nhanes-19882018"
TARGET_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
FILES = (
    "chemicals_clean.csv",
    "comments_clean.csv",
    "demographics_clean.csv",
    "dietary_clean.csv",
    "medications_clean.csv",
    "mortality_clean.csv",
    "occupation_clean.csv",
    "questionnaire_clean.csv",
    "response_clean.csv",
    "weights_clean.csv",
    "dictionary_drug_codes.csv",
    "dictionary_harmonized_categories.csv",
    "dictionary_nhanes.csv",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace files that already exist in data/raw",
    )
    args = parser.parse_args()

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for filename in FILES:
        destination = TARGET_DIR / filename
        if destination.exists() and not args.overwrite:
            print(f"Skipping existing file: {destination}")
            continue

        downloaded = Path(kagglehub.dataset_download(DATASET, path=filename))
        if not downloaded.is_file():
            raise FileNotFoundError(f"KaggleHub did not return a file for {filename}")
        shutil.copy2(downloaded, destination)
        print(f"Downloaded {filename} to {destination}")


if __name__ == "__main__":
    main()
