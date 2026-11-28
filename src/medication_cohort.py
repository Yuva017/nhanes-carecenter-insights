"""Analyze loaded medication data and prepare temporary review lists."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .sql_activity import capture_sql

SQL_DIR = Path(__file__).resolve().parents[1] / "database" / "sql" / "cohorts"
AgeBand = Literal["all", "under20", "20to39", "40to59", "60plus"]
AGE_BOUNDS = {
    "all": (None, None),
    "under20": (None, 19),
    "20to39": (20, 39),
    "40to59": (40, 59),
    "60plus": (60, None),
}
DrugClass = Annotated[str, StringConstraints(min_length=1, max_length=120)]


class MedicationReview(BaseModel):
    cycle_id: int | None = None
    age_band: AgeBand = "all"
    drug_classes: list[DrugClass] = Field(min_length=1, max_length=12)
    minimum_participants: int = Field(ge=1, le=2_147_483_647)


OPTIONS = text("SELECT cycle_id, period_label FROM public.survey_cycle ORDER BY start_year, cycle_id")
SUMMARY = text("""
    SELECT * FROM pg_temp.medication_cohort_summary(:cycle, :minimum_age, :maximum_age)
    ORDER BY participants DESC NULLS LAST, drug_class
""")
CANDIDATES = text("""
    INSERT INTO pg_temp.medication_review_candidates (drug_class, participants, entries)
    VALUES (:drug_class, :participants, :entries)
""")
BUILD_REVIEW = text("CALL pg_temp.build_medication_review(CAST(:selected AS text[]), :threshold)")
REVIEW_ROWS = text("""
    SELECT c.drug_class, c.participants, c.entries
    FROM pg_temp.medication_review_candidates AS c
    JOIN pg_temp.medication_review_list AS r USING (drug_class)
    ORDER BY c.participants DESC, c.drug_class
""")


def list_survey_periods(engine, queries):
    with engine.connect() as connection, capture_sql(connection, queries):
        return [dict(row) for row in connection.execute(OPTIONS).mappings()]


def analyze_medication_cohort(engine, cycle_id, age_band, queries, review=None):
    min_age, max_age = AGE_BOUNDS[age_band]
    with engine.connect() as connection, capture_sql(connection, queries):
        transaction = connection.begin()
        try:
            connection.exec_driver_sql("SET LOCAL statement_timeout = '10s'")
            connection.exec_driver_sql((SQL_DIR / "medication_cohort.sql").read_text(encoding="utf-8"))
            records = connection.execute(
                SUMMARY, {"cycle": cycle_id, "minimum_age": min_age, "maximum_age": max_age}
            ).mappings().all()
            cohort_size = records[0]["cohort_size"]
            rows = [
                {"drug_class": row["drug_class"], "participants": row["participants"], "entries": row["entries"]}
                for row in records if row["drug_class"] is not None
            ]
            result = {"cohort_size": cohort_size, "rows": rows}
            if review is not None:
                result["review"] = build_review(connection, rows, review)
        finally:
            transaction.rollback()
            if queries is not None:
                queries.append({"sql": "ROLLBACK", "status": "completed"})
    return result


def build_review(connection, rows, review):
    connection.exec_driver_sql((SQL_DIR / "medication_review.sql").read_text(encoding="utf-8"))
    if rows:
        connection.execute(CANDIDATES, rows)
    try:
        with connection.begin_nested():
            connection.execute(
                BUILD_REVIEW,
                {"selected": review.drug_classes, "threshold": review.minimum_participants},
            )
    except DBAPIError as error:
        if getattr(error.orig, "pgcode", None) not in {"P2001", "P2002"}:
            raise
        return {"status": "rejected", "reason": error.orig.diag.message_primary, "rows": []}
    return {
        "status": "accepted",
        "rows": [dict(row) for row in connection.execute(REVIEW_ROWS).mappings()],
    }
