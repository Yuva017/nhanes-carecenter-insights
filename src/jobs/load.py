"""Layer 3: stage transformed frames, then populate final relations."""

from pathlib import Path

from ..db import get_engine, run_sql_file
from .extract import extract_all
from .transform import transform_participant

STAGING_SCHEMA = "staging"


def ensure_staging(engine) -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql(f"CREATE SCHEMA IF NOT EXISTS {STAGING_SCHEMA};")


def stage_frame(engine, name: str, df) -> None:
    df.to_sql(name, engine, schema=STAGING_SCHEMA, if_exists="replace", index=False)


def run_pipeline(config: dict) -> None:
    raw_dir = Path(config["root"]) / config["data"]["raw_dir"]
    engine = get_engine()
    ensure_staging(engine)

    raw = extract_all(raw_dir, config["pipeline"]["cycles"])
    participants = transform_participant(
        raw["demographics"], config["pipeline"]["max_participants"]
    )
    stage_frame(engine, "participant", participants)
    # TODO: stage the remaining modules after their transforms are implemented

    run_sql_file(engine, Path(config["root"]) / "sql" / "load.sql")
