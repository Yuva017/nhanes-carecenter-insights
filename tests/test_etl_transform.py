import pandas as pd

from src.jobs.extract import extract_module
from src.jobs.transform import (
    transform_chemicals,
    transform_comments,
    transform_dietary,
    transform_medications,
    transform_participant,
    transform_physiological,
    transform_survey_cycle,
    transform_weights,
)


def test_extract_module_uses_clean_filename_and_filters_release_cycles(tmp_path):
    source = tmp_path / "demographics_clean.csv"
    pd.DataFrame(
        {
            "SEQN": [1, 2, 3],
            "SEQN_new": ["p1", "p2", "p3"],
            "SDDSRVYR": [1, -1, 1],
            "RIDAGEYR": [20, 30, 40],
        }
    ).to_csv(source, index=False)

    extracted = extract_module(
        tmp_path,
        "demographics",
        [1, 2],
        ["SEQN_new", "SDDSRVYR"],
        max_rows=2,
    )

    assert extracted["SEQN_new"].tolist() == ["p1", "p3"]


def test_participant_cycles_use_nhanes_period_labels():
    source = pd.DataFrame(
        {
            "SEQN": [1, 2, 3, 4],
            "SEQN_new": ["p1", "p2", "p3", "p4"],
            "SDDSRVYR": [-1, 1, 9, 10],
        }
    )

    participants = transform_participant(source)
    cycles = transform_survey_cycle(participants)

    assert cycles[["cycle_id", "period_label"]].to_dict("records") == [
        {"cycle_id": -1, "period_label": "1988-1994"},
        {"cycle_id": 1, "period_label": "1999-2000"},
        {"cycle_id": 9, "period_label": "2015-2016"},
        {"cycle_id": 10, "period_label": "2017-2018"},
    ]


def test_physiological_chart_data_averages_systolic_readings():
    source = pd.DataFrame(
        {
            "SEQN_new": ["p1"],
            "BMXBMI": [24.5],
            "BPXSY1": [120],
            "BPXSY2": [122],
            "BPXSY3": [None],
            "BPXSY4": [None],
        }
    )

    profile = transform_physiological(source, {"p1"})

    assert profile.loc[0, "body_mass_index"] == 24.5
    assert profile.loc[0, "systolic_bp"] == 121


def test_medication_class_comes_from_dictionary():
    medications = pd.DataFrame(
        {
            "SEQN_new": ["p1"],
            "RXDDRGID": ["a10061"],
            "RXDDRUG": ["Drug A"],
            "RXDDAYS": [30],
        }
    )
    dictionary = pd.DataFrame(
        {
            "RXDDRGID": ["a10061"],
            "RXDDRUG": ["Drug A"],
            "RXDDCN1A": ["CARDIOVASCULAR AGENTS"],
            "RXDICN1A": ["OTHER"],
        }
    )

    rows = transform_medications(medications, dictionary, {"p1"})

    assert rows.loc[0, "drug_class"] == "CARDIOVASCULAR AGENTS"
    assert rows.loc[0, "source_row_no"] == 1


def test_long_transforms_keep_only_selected_participants_and_values():
    participants = {"p1"}
    chemicals = transform_chemicals(
        pd.DataFrame(
            {"SEQN_new": ["p1", "p2"], "LBXGLU": [90, 100], "LBXTC": [None, 200]}
        ),
        participants,
        ["LBXGLU", "LBXTC"],
    )
    comments = transform_comments(
        pd.DataFrame({"SEQN_new": ["p1"], "LBDGLYLC": ["L"]}),
        participants,
        {"LBDGLYLC": "LBXGLY"},
    )
    weights = transform_weights(
        pd.DataFrame(
            {
                "SEQN_new": ["p1"],
                "WTMEC2YR": [1.5],
                "WTINT2YR": [None],
            }
        ),
        participants,
    )
    dietary = transform_dietary(
        pd.DataFrame(
            {"SEQN_new": ["p1", "p1"], "DRXTKCAL": [1800, 2000]}
        ),
        participants,
    )

    assert chemicals["measured_value"].tolist() == [90]
    assert comments[["analyte_code", "comment_code"]].to_dict("records") == [
        {"analyte_code": "LBXGLY", "comment_code": "L"}
    ]
    assert weights[["weight_code", "weight_value"]].to_dict("records") == [
        {"weight_code": "WTMEC2YR", "weight_value": 1.5}
    ]
    assert dietary["source_row_no"].tolist() == [1, 2]
