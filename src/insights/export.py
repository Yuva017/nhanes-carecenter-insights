"""Layer 5: run analytics queries and export JSON for the dashboard."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..db import get_engine

QUERIES_DIR = Path(__file__).resolve().parents[3] / "sql" / "queries"

# name -> (file, query marker). Each result is written to docs/data/<name>.json
ANALYTICS = {
    "bmi_by_age_cycle": ("01_selects.sql", "-- Q1"),
    "meds_below_detection": ("01_selects.sql", "-- Q2"),
    "meds_by_drug_class": ("01_selects.sql", "-- Q3"),
    "bmi_above_mean": ("01_selects.sql", "-- Q4"),
    "dietary_by_cycle": ("01_selects.sql", "-- Q5"),
}


def load_query(marker: str) -> str:
    sql = (QUERIES_DIR / "01_selects.sql").read_text()
    start = sql.index(marker)
    end = sql.find("\n-- Q", start + 4)
    return sql[start:end] if end != -1 else sql[start:]


def export_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    written = []
    for name, (_, marker) in ANALYTICS.items():
        df = pd.read_sql_query(load_query(marker), engine)
        path = out_dir / f"{name}.json"
        df.to_json(path, orient="records", indent=2)
        written.append(path)
    return written


if __name__ == "__main__":
    docs_data = Path(__file__).resolve().parents[3] / "docs" / "data"
    for p in export_all(docs_data):
        print(f"wrote {p}")
