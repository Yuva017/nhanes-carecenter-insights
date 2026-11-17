"""Configuration loading (config.yaml + .env)."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def load_config(path: Path | None = None) -> dict:
    cfg_path = path or ROOT / "config" / "config.yaml"
    with open(cfg_path) as fh:
        cfg = yaml.safe_load(fh)
    cfg["database_url"] = os.environ["DATABASE_URL"]
    cfg["root"] = str(ROOT)
    return cfg
