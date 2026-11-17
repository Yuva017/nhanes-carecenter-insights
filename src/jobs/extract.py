"""Layer 1: extract NHANES CSV modules into DataFrames."""

from collections.abc import Iterator, Sequence
from pathlib import Path

import pandas as pd

MODULE_FILES = {
    "demographics": "demographics_clean.csv",
    "dietary": "dietary_clean.csv",
    "medications": "medications_clean.csv",
    "mortality": "mortality_clean.csv",
    "occupation": "occupation_clean.csv",
    "questionnaire": "questionnaire_clean.csv",
    "chemicals": "chemicals_clean.csv",
    "comments": "comments_clean.csv",
    "weights": "weights_clean.csv",
    "response": "response_clean.csv",
}


def iter_module_chunks(
    raw_dir: Path,
    module: str,
    cycles: Sequence[int],
    columns: Sequence[str] | None = None,
    chunksize: int = 2_000,
    max_rows: int | None = None,
) -> Iterator[pd.DataFrame]:
    """Yield selected rows from a raw module, optionally in bounded chunks."""
    if max_rows is not None and max_rows < 1:
        raise ValueError("max_rows must be greater than zero")

    try:
        path = raw_dir / MODULE_FILES[module]
    except KeyError:
        raise ValueError(f"unknown NHANES module: {module}") from None

    if not path.is_file():
        raise FileNotFoundError(f"source file not found: {path}")

    available = pd.read_csv(path, nrows=0).columns.tolist()
    selected = (
        [column for column in available if column not in {"Unnamed: 0"}]
        if columns is None
        else [column for column in columns if column in available]
    )
    if not selected:
        raise ValueError(f"no requested columns found in {path}")

    dtype = {"SEQN_new": "string"} if "SEQN_new" in selected else None
    reader = pd.read_csv(
        path,
        usecols=selected,
        dtype=dtype,
        chunksize=chunksize,
        low_memory=False,
    )
    rows_yielded = 0
    for frame in reader:
        if "SDDSRVYR" in frame and cycles:
            frame["SDDSRVYR"] = pd.to_numeric(frame["SDDSRVYR"], errors="coerce")
            frame = frame[frame["SDDSRVYR"].isin(cycles)]
        if max_rows is not None:
            remaining = max_rows - rows_yielded
            if remaining <= 0:
                break
            frame = frame.head(remaining)
        if not frame.empty:
            yield frame
            rows_yielded += len(frame)
            if max_rows is not None and rows_yielded >= max_rows:
                break


def extract_module(
    raw_dir: Path,
    module: str,
    cycles: Sequence[int],
    columns: Sequence[str] | None = None,
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Read one module into a DataFrame for transformations."""
    chunks = list(
        iter_module_chunks(
            raw_dir,
            module,
            cycles,
            columns,
            chunksize=50_000,
            max_rows=max_rows,
        )
    )
    if not chunks:
        raise ValueError(f"no records for module '{module}' in {raw_dir}")
    return pd.concat(chunks, ignore_index=True)
