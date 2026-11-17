"""Layer 1: extract NHANES CSV modules into DataFrames."""

from pathlib import Path

import pandas as pd

# module name in data/raw -> file prefix in the Kaggle dataset
MODULE_FILES = {
    "demographics": "demographics",
    "dietary": "dietary",
    "medications": "medications",
    "mortality": "mortality",
    "occupation": "occupation",
    "questionnaire": "questionnaire",
    "chemicals": "chemicals",
    "comments": "comments",
    "weights": "weights",
    "response": "response",
}


def extract_module(raw_dir: Path, module: str, cycles: list[int]) -> pd.DataFrame:
    """Read one module's CSVs for the selected cycles."""
    frames = []
    for prefix in MODULE_FILES[module]:
        path = raw_dir / f"{prefix}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "SDDSRVYR" in df.columns and cycles:
            df = df[df["SDDSRVYR"].isin(cycles)]
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no source file found for module '{module}' in {raw_dir}")
    return pd.concat(frames, ignore_index=True)


def extract_all(raw_dir: Path, cycles: list[int]) -> dict[str, pd.DataFrame]:
    return {m: extract_module(raw_dir, m, cycles) for m in MODULE_FILES}
