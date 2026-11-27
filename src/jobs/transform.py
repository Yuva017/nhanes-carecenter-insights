"""Layer 2: transform raw NHANES frames into staging shapes."""

import pandas as pd

# The harmonized release uses -1 for NHANES III. Continuous cycles
# retain the CDC SDDSRVYR codes 1 through 10.
CYCLE_PERIODS = {
    -1: ("1988-1994", 1988, 1994),
    1: ("1999-2000", 1999, 2000),
    2: ("2001-2002", 2001, 2002),
    3: ("2003-2004", 2003, 2004),
    4: ("2005-2006", 2005, 2006),
    5: ("2007-2008", 2007, 2008),
    6: ("2009-2010", 2009, 2010),
    7: ("2011-2012", 2011, 2012),
    8: ("2013-2014", 2013, 2014),
    9: ("2015-2016", 2015, 2016),
    10: ("2017-2018", 2017, 2018),
}

SYSTOLIC_FIELDS = ("BPXSY1", "BPXSY2", "BPXSY3", "BPXSY4")
WEIGHT_FIELDS = (
    "WTMEC2YR",
    "WTINT2YR",
    "WTDRD1",
    "WTDR2D",
    "WTSA2YR",
    "WTSAF2YR",
    "WTMEC4YR",
    "WTINT4YR",
)


def _text(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(None, index=frame.index, dtype=object)
    values = frame[column].astype("string").str.strip().replace("", pd.NA)
    return values.astype(object).where(values.notna(), None)


def _number(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(float("nan"), index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _integer(frame: pd.DataFrame, column: str) -> pd.Series:
    return _number(frame, column).round().astype("Int64")


def _participants(
    frame: pd.DataFrame, participant_ids: set[str] | None = None
) -> pd.DataFrame:
    if "SEQN_new" not in frame:
        raise ValueError("source module is missing SEQN_new")
    result = frame.copy()
    result["participant_id"] = _text(result, "SEQN_new")
    result = result.dropna(subset=["participant_id"])
    result = result[result["participant_id"] != ""]
    if participant_ids is not None:
        result = result[result["participant_id"].isin(participant_ids)]
    return result


def transform_participant(
    demographics: pd.DataFrame, max_participants: int | None = None
) -> pd.DataFrame:
    frame = _participants(demographics)
    frame["source_seqn"] = _integer(frame, "SEQN")
    frame["cycle_id"] = _integer(frame, "SDDSRVYR")
    frame = frame.dropna(subset=["source_seqn", "cycle_id"])
    frame = frame.drop_duplicates("participant_id")
    if max_participants is not None and max_participants > 0:
        frame = frame.head(max_participants)
    frame["source_seqn"] = frame["source_seqn"].astype("Int64")
    frame["cycle_id"] = frame["cycle_id"].astype("int64")
    return frame[["participant_id", "source_seqn", "cycle_id"]].reset_index(drop=True)


def transform_survey_cycle(participants: pd.DataFrame) -> pd.DataFrame:
    cycle_ids = sorted(participants["cycle_id"].astype(int).unique())
    unknown = set(cycle_ids) - CYCLE_PERIODS.keys()
    if unknown:
        raise ValueError(f"unknown NHANES cycle IDs: {sorted(unknown)}")
    return pd.DataFrame(
        [
            {
                "cycle_id": cycle_id,
                "period_label": CYCLE_PERIODS[cycle_id][0],
                "start_year": CYCLE_PERIODS[cycle_id][1],
                "end_year": CYCLE_PERIODS[cycle_id][2],
            }
            for cycle_id in cycle_ids
        ]
    )


def transform_demographics(
    demographics: pd.DataFrame, participant_ids: set[str]
) -> pd.DataFrame:
    frame = _participants(demographics, participant_ids).drop_duplicates(
        "participant_id"
    )
    return pd.DataFrame(
        {
            "participant_id": frame["participant_id"],
            "age_years": _integer(frame, "RIDAGEYR"),
            "sex_code": _text(frame, "RIAGENDR"),
            "race_code": _text(frame, "RIDRETH1"),
            "poverty_ratio": _number(frame, "INDFMPIR"),
        }
    ).reset_index(drop=True)


def transform_mortality(
    mortality: pd.DataFrame, participant_ids: set[str]
) -> pd.DataFrame:
    frame = _participants(mortality, participant_ids).drop_duplicates(
        "participant_id"
    )
    return pd.DataFrame(
        {
            "participant_id": frame["participant_id"],
            "vital_status": _integer(frame, "MORTSTAT"),
            "followup_months": _integer(frame, "PERMTH_EXM"),
        }
    ).reset_index(drop=True)


def transform_questionnaire(
    questionnaire: pd.DataFrame, participant_ids: set[str]
) -> pd.DataFrame:
    frame = _participants(questionnaire, participant_ids).drop_duplicates(
        "participant_id"
    )
    return pd.DataFrame(
        {
            "participant_id": frame["participant_id"],
            "smoking_code": _text(frame, "SMQ020"),
            "diabetes_code": _text(frame, "DIQ010"),
        }
    ).reset_index(drop=True)


def transform_occupation(
    occupation: pd.DataFrame, participant_ids: set[str]
) -> pd.DataFrame:
    frame = _participants(occupation, participant_ids).drop_duplicates(
        "participant_id"
    )
    return pd.DataFrame(
        {
            "participant_id": frame["participant_id"],
            "employment_code": _text(frame, "OCD150"),
            "hours_worked": _number(frame, "OCQ180"),
        }
    ).reset_index(drop=True)


def transform_physiological(
    response: pd.DataFrame, participant_ids: set[str]
) -> pd.DataFrame:
    frame = _participants(response, participant_ids)
    frame["body_mass_index"] = _number(frame, "BMXBMI")
    systolic_fields = [field for field in SYSTOLIC_FIELDS if field in frame]
    if systolic_fields:
        frame["systolic_bp"] = frame[systolic_fields].apply(
            pd.to_numeric, errors="coerce"
        ).mean(axis=1)
    else:
        frame["systolic_bp"] = float("nan")
    return (
        frame.groupby("participant_id", as_index=False)[
            ["body_mass_index", "systolic_bp"]
        ]
        .mean()
        .reset_index(drop=True)
    )


def transform_dietary(
    dietary: pd.DataFrame, participant_ids: set[str]
) -> pd.DataFrame:
    frame = _participants(dietary, participant_ids)
    frame["amount"] = _number(frame, "DRXTKCAL")
    frame = frame.dropna(subset=["amount"])
    frame["source_row_no"] = (
        frame.groupby("participant_id").cumcount().add(1).astype("int64")
    )
    frame["dietary_code"] = "DRXTKCAL"
    return frame[
        ["participant_id", "source_row_no", "dietary_code", "amount"]
    ].reset_index(drop=True)


def transform_medications(
    medications: pd.DataFrame,
    drug_dictionary: pd.DataFrame,
    participant_ids: set[str],
) -> pd.DataFrame:
    frame = _participants(medications, participant_ids)
    frame["drug_code"] = _text(frame, "RXDDRGID")
    frame["drug_label"] = _text(frame, "RXDDRUG")
    frame["duration_days"] = _number(frame, "RXDDAYS")
    frame = frame.dropna(subset=["drug_code", "drug_label"], how="all")

    lookup = drug_dictionary.copy()
    lookup["drug_code"] = _text(lookup, "RXDDRGID")
    lookup["dictionary_label"] = _text(lookup, "RXDDRUG")
    lookup["drug_class"] = _text(lookup, "RXDDCN1A").combine_first(
        _text(lookup, "RXDICN1A")
    )
    lookup = lookup.dropna(subset=["drug_code"]).drop_duplicates("drug_code")
    frame = frame.merge(
        lookup[["drug_code", "dictionary_label", "drug_class"]],
        on="drug_code",
        how="left",
        validate="many_to_one",
    )
    frame["drug_label"] = frame["drug_label"].combine_first(
        frame["dictionary_label"]
    )
    frame["drug_class"] = frame["drug_class"].fillna("Unclassified")
    frame["source_row_no"] = (
        frame.groupby("participant_id").cumcount().add(1).astype("int64")
    )
    return frame[
        [
            "participant_id",
            "source_row_no",
            "drug_code",
            "duration_days",
            "drug_label",
            "drug_class",
        ]
    ].reset_index(drop=True)


def transform_chemical_analytes(
    dictionary: pd.DataFrame, available_codes: set[str], selected_codes: list[str]
) -> pd.DataFrame:
    metadata = dictionary.dropna(subset=["variable_codename_use"]).copy()
    metadata = metadata.drop_duplicates("variable_codename_use").set_index(
        "variable_codename_use"
    )
    codes = selected_codes or sorted(available_codes.intersection(metadata.index))
    missing = set(codes) - available_codes
    if missing:
        raise ValueError(f"configured chemical analytes not found: {sorted(missing)}")
    records = []
    for code in codes:
        if code not in metadata.index:
            continue
        row = metadata.loc[code]
        records.append(
            {
                "analyte_code": code,
                "analyte_label": row.get("variable_description_use") or code,
                "measurement_unit": row.get("units"),
                "cas_number": row.get("cas_num"),
            }
        )
    result = pd.DataFrame.from_records(records)
    result["analyte_label"] = result["analyte_label"].fillna(
        result["analyte_code"]
    )
    for field, max_length in (("measurement_unit", 60), ("cas_number", 40)):
        result[field] = _text(result, field)
        result[field] = result[field].map(
            lambda value: value[:max_length] if value is not None else None
        )
    return result


def transform_chemicals(
    chemicals: pd.DataFrame,
    participant_ids: set[str],
    analyte_codes: list[str],
) -> pd.DataFrame:
    frame = _participants(chemicals, participant_ids)
    value_columns = [code for code in analyte_codes if code in frame]
    long = frame[["participant_id", *value_columns]].melt(
        id_vars="participant_id",
        value_vars=value_columns,
        var_name="analyte_code",
        value_name="measured_value",
    )
    long["measured_value"] = pd.to_numeric(long["measured_value"], errors="coerce")
    long = long.dropna(subset=["measured_value"]).drop_duplicates(
        ["participant_id", "analyte_code"]
    )
    return long.reset_index(drop=True)


def transform_comments(
    comments: pd.DataFrame,
    participant_ids: set[str],
    comment_mapping: dict[str, str],
) -> pd.DataFrame:
    frame = _participants(comments, participant_ids)
    value_columns = [column for column in comment_mapping if column in frame]
    long = frame[["participant_id", *value_columns]].melt(
        id_vars="participant_id",
        value_vars=value_columns,
        var_name="comment_field",
        value_name="comment_code",
    )
    long = long.dropna(subset=["comment_code"])
    long["analyte_code"] = long["comment_field"].map(comment_mapping)
    long["comment_code"] = _text(long, "comment_code")
    long = long.dropna(subset=["comment_code"]).drop_duplicates(
        ["participant_id", "analyte_code"]
    )
    return long[["participant_id", "analyte_code", "comment_code"]].reset_index(
        drop=True
    )


def transform_weights(
    weights: pd.DataFrame, participant_ids: set[str]
) -> pd.DataFrame:
    frame = _participants(weights, participant_ids)
    value_columns = [column for column in WEIGHT_FIELDS if column in frame]
    long = frame[["participant_id", *value_columns]].melt(
        id_vars="participant_id",
        value_vars=value_columns,
        var_name="weight_code",
        value_name="weight_value",
    )
    long["weight_value"] = pd.to_numeric(long["weight_value"], errors="coerce")
    long = long.dropna(subset=["weight_value"]).drop_duplicates(
        ["participant_id", "weight_code"]
    )
    return long.reset_index(drop=True)
