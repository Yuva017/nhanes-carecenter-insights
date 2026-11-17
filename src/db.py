"""Database engine and helpers."""

import yaml
from sqlalchemy import create_engine, text

from .config import load_config


def get_engine():
    cfg = load_config()
    return create_engine(cfg["database_url"], pool_size=cfg["database"].get("pool_size", 5))


def run_sql_file(engine, path) -> None:
    """Execute a .sql file as a single script."""
    sql = open(path, encoding="utf-8").read()
    with engine.begin() as conn:
        conn.execute(text(sql))
