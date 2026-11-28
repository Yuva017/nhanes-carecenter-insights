"""Serve the CareCenter dashboard and its read-only aggregate queries."""

from functools import lru_cache
import json
import logging

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .analytics.export import ANALYTICS, PROJECT_ROOT, load_query
from .database_operations import Scenario, run_medication_operation
from .db import get_engine
from .medication_cohort import AgeBand, MedicationReview, analyze_medication_cohort, list_survey_periods
from .sql_activity import capture_sql

logger = logging.getLogger(__name__)
app = FastAPI(title="CareCenter Insights")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yuva017.github.io"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@lru_cache(maxsize=1)
def _engine():
    return get_engine()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/charts/{dataset}", response_class=Response)
@app.get("/data/{dataset}.json", response_class=Response, include_in_schema=False)
def dashboard_data(dataset: str, include_sql: bool = False):
    query_file = ANALYTICS.get(dataset)
    if query_file is None:
        raise HTTPException(status_code=404, detail="Chart dataset not found")
    queries = [] if include_sql else None
    try:
        query = text(load_query(query_file))
        with _engine().connect() as connection, capture_sql(connection, queries):
            rows = pd.read_sql_query(query, connection)
    except (KeyError, OSError, SQLAlchemyError) as error:
        logger.warning("Could not load chart %s (%s)", dataset, type(error).__name__)
        return unavailable("Chart data is unavailable", queries)
    rows_json = rows.to_json(orient="records")
    headers = {
        "Cache-Control": "no-store",
        "X-CareCenter-Data-Source": "PostgreSQL",
    }
    if include_sql:
        return JSONResponse({"rows": json.loads(rows_json), "queries": queries}, headers=headers)
    return Response(rows_json, media_type="application/json", headers=headers)


def unavailable(message: str, queries):
    body = {"detail": message}
    if queries is not None:
        body["queries"] = queries
    return JSONResponse(body, status_code=503, headers={"Cache-Control": "no-store"})


@app.post("/api/operations/medications/{scenario}")
def medication_operation(scenario: Scenario, include_sql: bool = False):
    queries = [] if include_sql else None
    try:
        operation = run_medication_operation(_engine(), scenario, queries)
        if include_sql:
            operation["queries"] = queries
        return JSONResponse(operation, headers={"Cache-Control": "no-store"})
    except (KeyError, OSError, SQLAlchemyError, RuntimeError) as error:
        logger.warning("Could not run medication operation %s (%s)", scenario, type(error).__name__)
        return unavailable("Database operations are unavailable", queries)


@app.get("/api/medication-cohort/options")
def medication_cohort_options(include_sql: bool = False):
    queries = [] if include_sql else None
    try:
        result = {"periods": list_survey_periods(_engine(), queries)}
    except (KeyError, OSError, SQLAlchemyError) as error:
        logger.warning("Medication cohort options unavailable (%s)", type(error).__name__)
        return unavailable("Survey periods are unavailable", queries)
    if queries is not None:
        result["queries"] = queries
    return JSONResponse(result, headers={"Cache-Control": "no-store"})


@app.get("/api/medication-cohort")
def medication_cohort(cycle_id: int | None = None, age_band: AgeBand = "all", include_sql: bool = False):
    return cohort_response(cycle_id, age_band, include_sql)


@app.post("/api/medication-cohort/review")
def medication_cohort_review(review: MedicationReview, include_sql: bool = False):
    return cohort_response(review.cycle_id, review.age_band, include_sql, review)


def cohort_response(cycle_id, age_band, include_sql, review=None):
    queries = [] if include_sql else None
    try:
        result = analyze_medication_cohort(_engine(), cycle_id, age_band, queries, review)
    except (KeyError, OSError, SQLAlchemyError) as error:
        logger.warning("Medication cohort unavailable (%s)", type(error).__name__)
        return unavailable("Medication cohort data is unavailable", queries)
    if queries is not None:
        result["queries"] = queries
    return JSONResponse(result, headers={"Cache-Control": "no-store"})


class DashboardFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        # Allow conditional requests while ensuring the browser checks for deploys.
        response.headers["Cache-Control"] = "no-cache"
        return response


# Register the API and compatibility route before serving the dashboard assets.
app.mount("/", DashboardFiles(directory=PROJECT_ROOT / "public", html=True), name="dashboard")
