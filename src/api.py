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
from .sql_activity import capture_sql

logger = logging.getLogger(__name__)
app = FastAPI(title="CareCenter Insights")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yuva017.github.io"],
    allow_methods=["GET", "POST"],
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


# Register the API and compatibility route before serving the dashboard assets.
app.mount("/", StaticFiles(directory=PROJECT_ROOT / "public", html=True), name="dashboard")
