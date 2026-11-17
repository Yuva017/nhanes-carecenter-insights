"""Layer 2: transform raw NHANES frames into staging shapes."""

import pandas as pd


def transform_participant(demographics: pd.DataFrame, max_participants: int) -> pd.DataFrame:
    df = demographics.rename(columns={"SEQN_new": "participant_id", "SEQN": "source_seqn"})
    df = df.dropna(subset=["participant_id"]).drop_duplicates("participant_id")
    df["cycle_id"] = df["SDDSRVYR"].astype(int)
    cols = ["participant_id", "source_seqn", "cycle_id"]
    # TODO map remaining demographic fields into demographic_profile columns
    return df[cols].head(max_participants)


def transform_demographics(demographics: pd.DataFrame) -> pd.DataFrame:
    df = demographics.rename(columns={"SEQN_new": "participant_id"})
    # TODO map age, sex, race, poverty ratio columns per dictionary_nhanes.csv
    return df


def pivot_chemicals(chemicals: pd.DataFrame) -> pd.DataFrame:
    """Wide chemical columns -> long (participant_id, analyte_code, measured_value)."""
    id_cols = ["participant_id"]
    long = chemicals.melt(id_vars=id_cols, var_name="analyte_code", value_name="measured_value")
    return long.dropna(subset=["measured_value"])
