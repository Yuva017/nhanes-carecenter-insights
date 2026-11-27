"""Layer 5: run analytics queries and export JSON for the dashboard."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..db import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUERIES_DIR = PROJECT_ROOT / "database" / "sql"
DEFAULT_OUT_DIR = PROJECT_ROOT / "public" / "data"

# Map each dashboard export to the SQL operation that produces it.
ANALYTICS = {
    "bmi_by_age_cycle": "dashboard/bmi_by_age_cycle.sql",
    "meds_by_drug_class": "dashboard/medication_use_by_drug_class.sql",
    "dietary_by_cycle": "dashboard/dietary_intake_by_cycle.sql",
    "coverage_by_cycle": "dashboard/coverage_by_cycle.sql",
    "systolic_by_age": "dashboard/systolic_by_age.sql",
    "medication_records_per_participant": "dashboard/medication_records_per_participant.sql",
}


def load_query(query_path: str) -> str:
    return (QUERIES_DIR / query_path).read_text(encoding="utf-8")


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
