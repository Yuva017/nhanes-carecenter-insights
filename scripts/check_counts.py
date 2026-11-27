"""Row counts per relation; verifies the >= 3000 total for Phase 2."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from src.db import get_engine

TABLES = [
    "survey_cycle", "participant", "demographic_profile", "mortality_profile",
    "questionnaire_profile", "occupation_profile", "physiological_profile",
    "dietary_entry", "drug_reference", "medication_entry", "chemical_analyte",
    "chemical_result", "chemical_comment", "survey_weight",
]


def main() -> None:
    engine = get_engine()
    total = 0
    with engine.connect() as conn:
        for t in TABLES:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
            total += n
            print(f"{t:24s} {n:>8d}")
    print("-" * 33)
    print(f"{'TOTAL':24s} {total:>8d}")


if __name__ == "__main__":
    main()
