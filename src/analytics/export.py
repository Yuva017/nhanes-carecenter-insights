"""Layer 5: run analytics queries and export JSON for the dashboard."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..db import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUERIES_FILE = PROJECT_ROOT / "database" / "sql" / "01_selects.sql"
DEFAULT_OUT_DIR = PROJECT_ROOT / "public" / "data"

# Export only aggregate results used by the public charts.
ANALYTICS = {
    "bmi_by_age_cycle": "-- Q1",
    "meds_by_drug_class": "-- Q3",
    "dietary_by_cycle": "-- Q5",
}


def load_query(marker: str) -> str:
    sql = QUERIES_FILE.read_text(encoding="utf-8")
    start = sql.index(marker)
    end = sql.find("\n-- Q", start + 4)
    return sql[start:end] if end != -1 else sql[start:]


def export_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    written = []
    for name, marker in ANALYTICS.items():
        df = pd.read_sql_query(load_query(marker), engine)
        path = out_dir / f"{name}.json"
        df.to_json(path, orient="records", indent=2)
        written.append(path)
    return written


if __name__ == "__main__":
    for p in export_all(DEFAULT_OUT_DIR):
        print(f"wrote {p}")
