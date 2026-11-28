"""Run the repository's SQL validation exercises from the dashboard."""

from typing import Literal

from sqlparse import split

from .database_validation import VALIDATION_SCRIPT
from .sql_activity import capture_sql

ValidationExercise = Literal["schema", "queries", "transactions", "normalization", "concurrency", "performance"]
SCHEMA_FILE = "schema/relational_schema.sql"
EXERCISES = {
    "schema": (SCHEMA_FILE,),
    "queries": (SCHEMA_FILE, "queries/query_operation.sql"),
    "transactions": (SCHEMA_FILE, "transactions/routine_and_transaction.sql"),
    "normalization": (SCHEMA_FILE, "normalization/normal_form.sql"),
    "concurrency": ("concurrency/concurrency_control.sql",),
    "performance": ("performance/index_and_query_plan.sql",),
}
PREVIEW_ROWS = 50


def run_dashboard_validation(engine, exercise: ValidationExercise, queries):
    *setup_files, exercise_file = EXERCISES[exercise]
    with engine.connect() as connection:
        connection = connection.execution_options(isolation_level="AUTOCOMMIT")
        # Some exercises commit transactions. Closing this dedicated session
        # removes their temporary tables, indexes, views, and routines.
        connection.detach()
        with capture_sql(connection, queries):
            connection.exec_driver_sql("SET search_path TO pg_temp, pg_catalog")
            connection.exec_driver_sql("SET statement_timeout = '10s'")
            for setup_file in setup_files:
                run_exercise_file(connection, setup_file, report_results=False)
            count, outputs = run_exercise_file(connection, exercise_file, report_results=True)
    return {"file": exercise_file, "statements_executed": count, "outputs": outputs}


def run_exercise_file(connection, relative_path, *, report_results):
    statements = split((VALIDATION_SCRIPT.parent / relative_path).read_text(encoding="utf-8"))
    notices = connection.connection.dbapi_connection.notices
    outputs = []
    for index, statement in enumerate(statements, start=1):
        notices.clear()
        with connection.exec_driver_sql(statement, execution_options={"no_parameters": True}) as result:
            if report_results and (result.returns_rows or notices):
                keys = list(result.keys()) if result.returns_rows else []
                fields = [i for i, key in enumerate(keys) if key != "current_database"]
                rows = result.fetchmany(PREVIEW_ROWS + 1) if result.returns_rows else []
                outputs.append({
                    "statement": index,
                    "columns": [keys[i] for i in fields],
                    "rows": [[row[i] for i in fields] for row in rows[:PREVIEW_ROWS]],
                    "truncated": len(rows) > PREVIEW_ROWS,
                    "notices": [notice.strip() for notice in notices],
                })
    return len(statements), outputs
