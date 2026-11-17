"""Layer 3: stage transformed frames, then populate final relations."""

from pathlib import Path
from typing import Callable, Iterator

import pandas as pd

from ..db import get_engine, run_sql_file
from .extract import extract_module, iter_module_chunks
from .transform import (
    WEIGHT_FIELDS,
    transform_chemical_analytes,
    transform_comments,
    transform_demographics,
    transform_dietary,
    transform_medications,
    transform_mortality,
    transform_occupation,
    transform_participant,
    transform_physiological,
    transform_questionnaire,
    transform_survey_cycle,
    transform_chemicals,
    transform_weights,
)

STAGING_SCHEMA = "staging"
PARTICIPANT_COLUMNS = ("SEQN", "SEQN_new", "SDDSRVYR")
MODULE_COLUMNS = {
    "demographics": (
        *PARTICIPANT_COLUMNS,
        "RIDAGEYR",
        "RIAGENDR",
        "RIDRETH1",
        "INDFMPIR",
    ),
    "mortality": (*PARTICIPANT_COLUMNS, "MORTSTAT", "PERMTH_EXM"),
    "questionnaire": (*PARTICIPANT_COLUMNS, "SMQ020", "DIQ010"),
    "occupation": (*PARTICIPANT_COLUMNS, "OCD150", "OCQ180"),
    "response": (*PARTICIPANT_COLUMNS, "BMXBMI", "BPXSY1", "BPXSY2", "BPXSY3", "BPXSY4"),
    "dietary": (*PARTICIPANT_COLUMNS, "DRXTKCAL"),
    "medications": (
        *PARTICIPANT_COLUMNS,
        "RXDDRGID",
        "RXDDRUG",
        "RXDDAYS",
    ),
}
CHUNK_SIZE = 2_000


def ensure_staging(engine) -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql(f"CREATE SCHEMA IF NOT EXISTS {STAGING_SCHEMA}")


def stage_frame(engine, name: str, frame: pd.DataFrame, if_exists: str = "replace") -> None:
    if frame.empty:
        raise ValueError(f"refusing to stage an empty DataFrame: {name}")
    frame.to_sql(
        name,
        engine,
        schema=STAGING_SCHEMA,
        if_exists=if_exists,
        index=False,
        chunksize=10_000,
    )


def _stage_chunks(
    engine, name: str, chunks: Iterator[pd.DataFrame]
) -> None:
    mode = "replace"
    staged = False
    for frame in chunks:
        if frame.empty:
            if not staged:
                frame.to_sql(
                    name,
                    engine,
                    schema=STAGING_SCHEMA,
                    if_exists=mode,
                    index=False,
                )
                mode = "append"
                staged = True
            continue
        stage_frame(engine, name, frame, if_exists=mode)
        mode = "append"
        staged = True
    if not staged:
        raise ValueError(f"no records were available to stage for {name}")


def _dictionary(raw_dir: Path, filename: str, columns: tuple[str, ...]) -> pd.DataFrame:
    path = raw_dir / filename
    if not path.is_file():
        raise FileNotFoundError(f"dictionary file not found: {path}")
    header = pd.read_csv(path, nrows=0).columns
    selected = [column for column in columns if column in header]
    missing = set(columns) - set(selected)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    return pd.read_csv(path, usecols=selected, low_memory=False)


def _module_frame(
    raw_dir: Path, module: str, cycles: list[int], max_rows: int | None
) -> pd.DataFrame:
    return extract_module(
        raw_dir, module, cycles, MODULE_COLUMNS[module], max_rows=max_rows
    )


def _stage_module(
    engine,
    raw_dir: Path,
    module: str,
    cycles: list[int],
    table: str,
    transform: Callable[[pd.DataFrame, set[str]], pd.DataFrame],
    participant_ids: set[str],
    max_rows: int | None,
) -> None:
    frame = _module_frame(raw_dir, module, cycles, max_rows)
    stage_frame(engine, table, transform(frame, participant_ids))


def run_pipeline(config: dict) -> None:
    raw_dir = Path(config["root"]) / config["data"]["raw_dir"]
    cycles = config["pipeline"]["cycles"]
    max_participants = config["pipeline"].get("max_participants")
    max_rows = config["pipeline"].get("max_rows_per_module")
    engine = get_engine()
    ensure_staging(engine)

    demographics_source = extract_module(
        raw_dir,
        "demographics",
        cycles,
        MODULE_COLUMNS["demographics"],
        max_rows=max_rows,
    )
    participants = transform_participant(demographics_source, max_participants)
    if participants.empty:
        raise ValueError("no participants were found in the selected survey cycles")

    participant_ids = set(participants["participant_id"])
    stage_frame(engine, "survey_cycle", transform_survey_cycle(participants))
    stage_frame(engine, "participant", participants)
    stage_frame(
        engine,
        "demographic_profile",
        transform_demographics(demographics_source, participant_ids),
    )
    del demographics_source

    for module, table, transform in (
        ("mortality", "mortality_profile", transform_mortality),
        ("questionnaire", "questionnaire_profile", transform_questionnaire),
        ("occupation", "occupation_profile", transform_occupation),
        ("response", "physiological_profile", transform_physiological),
    ):
        _stage_module(
            engine,
            raw_dir,
            module,
            cycles,
            table,
            transform,
            participant_ids,
            max_rows,
        )

    dietary = _module_frame(raw_dir, "dietary", cycles, max_rows)
    stage_frame(engine, "dietary_entry", transform_dietary(dietary, participant_ids))
    del dietary

    drug_dictionary = _dictionary(
        raw_dir,
        "dictionary_drug_codes.csv",
        ("RXDDRGID", "RXDDRUG", "RXDDCN1A", "RXDICN1A"),
    )
    medications = _module_frame(raw_dir, "medications", cycles, max_rows)
    stage_frame(
        engine,
        "medication_entry",
        transform_medications(medications, drug_dictionary, participant_ids),
    )
    del medications, drug_dictionary

    dictionary = _dictionary(
        raw_dir,
        "dictionary_nhanes.csv",
        (
            "variable_codename_use",
            "variable_description_use",
            "units",
            "cas_num",
            "comment_codename_use",
        ),
    )
    chemical_header = pd.read_csv(
        raw_dir / "chemicals_clean.csv", nrows=0
    ).columns
    chemical_columns = set(chemical_header) - {
        "SEQN",
        "SEQN_new",
        "SDDSRVYR",
        "Unnamed: 0",
    }
    chemical_metadata = transform_chemical_analytes(
        dictionary,
        chemical_columns,
        config["pipeline"].get("analytes", []),
    )
    analyte_codes = chemical_metadata["analyte_code"].tolist()
    stage_frame(engine, "chemical_analyte", chemical_metadata)

    chemical_chunks = (
        transform_chemicals(chunk, participant_ids, analyte_codes)
        for chunk in iter_module_chunks(
            raw_dir,
            "chemicals",
            cycles,
            (*PARTICIPANT_COLUMNS, *analyte_codes),
            chunksize=CHUNK_SIZE,
            max_rows=max_rows,
        )
    )
    _stage_chunks(engine, "chemical_result", chemical_chunks)

    comment_header = pd.read_csv(raw_dir / "comments_clean.csv", nrows=0).columns
    comment_columns = set(comment_header)
    comment_mapping = {
        comment: analyte
        for analyte, comment in dictionary[
            ["variable_codename_use", "comment_codename_use"]
        ]
        .dropna()
        .itertuples(index=False, name=None)
        if comment in comment_columns and analyte in analyte_codes
    }
    comment_chunks = (
        transform_comments(chunk, participant_ids, comment_mapping)
        for chunk in iter_module_chunks(
            raw_dir,
            "comments",
            cycles,
            (*PARTICIPANT_COLUMNS, *comment_mapping),
            chunksize=CHUNK_SIZE,
            max_rows=max_rows,
        )
    )
    _stage_chunks(engine, "chemical_comment", comment_chunks)
    del dictionary, chemical_metadata

    weight_columns = [
        column
        for column in WEIGHT_FIELDS
        if column in pd.read_csv(raw_dir / "weights_clean.csv", nrows=0).columns
    ]
    weight_chunks = (
        transform_weights(chunk, participant_ids)
        for chunk in iter_module_chunks(
            raw_dir,
            "weights",
            cycles,
            (*PARTICIPANT_COLUMNS, *weight_columns),
            chunksize=CHUNK_SIZE,
            max_rows=max_rows,
        )
    )
    _stage_chunks(engine, "survey_weight", weight_chunks)

    run_sql_file(engine, Path(config["root"]) / "database" / "load.sql")
