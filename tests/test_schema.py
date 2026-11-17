"""Schema sanity tests (run with a loaded dev database)."""

import os

import pytest
from sqlalchemy import create_engine, inspect, text

URL = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(URL is None, reason="DATABASE_URL not set")

EXPECTED_TABLES = {
    "survey_cycle", "participant", "demographic_profile", "mortality_profile",
    "questionnaire_profile", "occupation_profile", "physiological_profile",
    "dietary_entry", "drug_reference", "medication_entry", "chemical_analyte",
    "chemical_result", "chemical_comment", "survey_weight",
}


def test_all_tables_exist():
    engine = create_engine(URL)
    names = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES <= names


def test_minimum_record_total():
    engine = create_engine(URL)
    with engine.connect() as conn:
        total = sum(
            conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
            for t in EXPECTED_TABLES
        )
    assert total >= 3000
