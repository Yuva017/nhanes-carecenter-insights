"""Configuration loading (config.yaml + .env)."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def load_config(path: Path | None = None) -> dict:
    cfg_path = path or ROOT / "config" / "config.yaml"
    with open(cfg_path) as fh:
        cfg = yaml.safe_load(fh)
    database_url = os.environ["DATABASE_URL"]
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://", "postgresql+psycopg2://", 1
        )
    elif database_url.startswith("postgresql+psycopg://"):
        database_url = database_url.replace(
            "postgresql+psycopg://", "postgresql+psycopg2://", 1
        )
    cfg["database_url"] = database_url
    cfg["root"] = str(ROOT)
    return cfg
