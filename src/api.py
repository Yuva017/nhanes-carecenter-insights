"""Serve the CareCenter dashboard and its read-only aggregate queries."""

from functools import lru_cache
import logging

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .analytics.export import ANALYTICS, PROJECT_ROOT, load_query
from .db import get_engine

logger = logging.getLogger(__name__)
app = FastAPI(title="CareCenter Insights")


@lru_cache(maxsize=1)
def _engine():
    return get_engine()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/data/{dataset}.json", response_class=Response)
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
        headers={"Cache-Control": "no-store"},
    )


# Match the dashboard's existing relative data/*.json URLs before serving files.
app.mount("/", StaticFiles(directory=PROJECT_ROOT / "public", html=True), name="dashboard")
