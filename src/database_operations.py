"""Exercise fixed PostgreSQL operations on temporary CareCenter sample records."""

from pathlib import Path
from typing import Literal

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .sql_activity import capture_sql

Scenario = Literal["summary", "record", "reject"]
SETUP_SQL = (
    Path(__file__).resolve().parents[1]
    / "database" / "validation" / "transactions" / "medication_workbench.sql"
)
SUMMARY = text("""
    SELECT status, pg_temp.workbench_medication_count(case_id) AS medication_count
    FROM pg_temp.workbench_case WHERE case_id = 1
""")
RECORD = text("CALL pg_temp.workbench_record_medication(1, :code)")


def run_medication_operation(engine, scenario: Scenario, queries: list | None = None) -> dict:
    with engine.connect() as connection, capture_sql(connection, queries):
        transaction = connection.begin()
        try:
            connection.exec_driver_sql("SET LOCAL statement_timeout = '5s'")
            connection.exec_driver_sql(SETUP_SQL.read_text(encoding="utf-8"))
            before = dict(connection.execute(SUMMARY).mappings().one())
            trigger = "Not invoked"
            steps = ["Read the sample case with the medication-count function."]
            if scenario == "record":
                connection.execute(RECORD, {"code": "SAMPLE-RX"})
                trigger = "Accepted valid code"
                steps.append("Called the procedure. The trigger accepted SAMPLE-RX.")
            elif scenario == "reject":
                try:
                    with connection.begin_nested():
                        connection.execute(RECORD, {"code": "UNKNOWN-RX"})
                except DBAPIError as error:
                    if getattr(error.orig, "pgcode", None) != "P2001":
                        raise
                    trigger = "Rejected invalid code (P2001)"
                    steps.append("The trigger rejected UNKNOWN-RX. Rollback to the savepoint undid the procedure's status update.")
                else:
                    raise RuntimeError("The trigger should have rejected the unknown sample drug code.")
            after = dict(connection.execute(SUMMARY).mappings().one())
            steps.append("Read the case again before discarding the temporary data.")
        finally:
            transaction.rollback()
            if queries is not None:
                queries.append({"sql": "ROLLBACK", "status": "completed"})
    return {"before": before, "after": after, "trigger": trigger, "steps": steps}
