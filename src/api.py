"""Serve the CareCenter dashboard and its read-only aggregate queries."""

from functools import lru_cache
import logging

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .analytics.export import ANALYTICS, PROJECT_ROOT, load_query
from .database_operations import Scenario, run_medication_operation
from .db import get_engine

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
def dashboard_data(dataset: str):
    query_file = ANALYTICS.get(dataset)
    if query_file is None:
        raise HTTPException(status_code=404, detail="Chart dataset not found")
    try:
        query = text(load_query(query_file))
        with _engine().connect() as connection:
            rows = pd.read_sql_query(query, connection)
    except (KeyError, OSError, SQLAlchemyError) as error:
        logger.warning("Could not load chart %s (%s)", dataset, type(error).__name__)
        raise HTTPException(status_code=503, detail="Chart data is unavailable") from None
    return Response(
        rows.to_json(orient="records"),
        media_type="application/json",
        headers={
            "Cache-Control": "no-store",
            "X-CareCenter-Data-Source": "PostgreSQL",
        },
    )


@app.post("/api/operations/medications/{scenario}")
def medication_operation(scenario: Scenario):
    try:
        return run_medication_operation(_engine(), scenario)
    except (KeyError, OSError, SQLAlchemyError, RuntimeError) as error:
        logger.warning("Could not run medication operation %s (%s)", scenario, type(error).__name__)
        raise HTTPException(status_code=503, detail="Database operations are unavailable") from None


# Register the API and compatibility route before serving the dashboard assets.
app.mount("/", StaticFiles(directory=PROJECT_ROOT / "public", html=True), name="dashboard")
