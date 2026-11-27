"""Run the CareCenter database checks in one PostgreSQL client session."""

from pathlib import Path
import shutil
import subprocess

VALIDATION_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "validation"
    / "run_validation.sql"
)


def run_database_validation(database: str) -> int:
    """Stream the validation statements and results to the caller's terminal."""
    if not database or "=" in database or "://" in database:
        raise ValueError("Use a database name and configure the connection with libpq settings.")
    client = shutil.which("psql")
    if client is None:
        raise FileNotFoundError("Install the PostgreSQL psql client and put it on PATH.")
    if not VALIDATION_SCRIPT.is_file():
        raise FileNotFoundError(f"SQL validation entry point is missing: {VALIDATION_SCRIPT}")

    # A single session preserves temporary tables and explicit transaction
    # boundaries, and psql resolves each include relative to run_validation.sql.
    result = subprocess.run(
        [
            client,
            "--no-psqlrc",
            "--no-password",
            "--echo-all",
            "--pset=pager=off",
            f"--dbname={database}",
            f"--file={VALIDATION_SCRIPT}",
        ],
        check=False,
    )
    return result.returncode
