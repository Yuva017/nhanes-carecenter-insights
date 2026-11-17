-- CareCenter: 14-relation NHANES schema (BCNF), per Phase 1 report
BEGIN;

CREATE TABLE IF NOT EXISTS survey_cycle (
    cycle_id      INTEGER     PRIMARY KEY,
    period_label  VARCHAR(25) NOT NULL,
    start_year    SMALLINT    NOT NULL,
    end_year      SMALLINT    NOT NULL
);

CREATE TABLE IF NOT EXISTS participant (
    participant_id   VARCHAR(32) PRIMARY KEY,   -- harmonized SEQN_new
    source_seqn      BIGINT      NOT NULL,
    cycle_id         INTEGER     NOT NULL,
    CONSTRAINT fk_participant_cycle FOREIGN KEY (cycle_id)
        REFERENCES survey_cycle(cycle_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS demographic_profile (
    participant_id  VARCHAR(32)  PRIMARY KEY,
    age_years       SMALLINT,
    sex_code        VARCHAR(30),
    race_code       VARCHAR(40),
    poverty_ratio   NUMERIC(8,3),
    CONSTRAINT fk_demo_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mortality_profile (
    participant_id     VARCHAR(32) PRIMARY KEY,
    vital_status       SMALLINT,
    followup_months    INTEGER,
    CONSTRAINT fk_mort_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS questionnaire_profile (
    participant_id  VARCHAR(32) PRIMARY KEY,
    smoking_code    VARCHAR(40),
    diabetes_code   VARCHAR(40),
    CONSTRAINT fk_quest_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS occupation_profile (
    participant_id   VARCHAR(32) PRIMARY KEY,
    employment_code  VARCHAR(40),
    hours_worked     NUMERIC(6,1),
    CONSTRAINT fk_occ_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS physiological_profile (
    participant_id     VARCHAR(32) PRIMARY KEY,
    body_mass_index    NUMERIC(7,2),
    systolic_bp        NUMERIC(7,2),
    CONSTRAINT fk_phys_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dietary_entry (
    dietary_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    participant_id  VARCHAR(32) NOT NULL,
    source_row_no   INTEGER     NOT NULL,
    dietary_code    VARCHAR(80),
    amount          NUMERIC(16,5),
    CONSTRAINT fk_diet_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE,
    CONSTRAINT uq_diet_participant_row UNIQUE (participant_id, source_row_no)
);

CREATE TABLE IF NOT EXISTS drug_reference (
    drug_code   VARCHAR(80) PRIMARY KEY,
    drug_label  TEXT,
    drug_class  VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS medication_entry (
    medication_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    participant_id  VARCHAR(32) NOT NULL,
    source_row_no   INTEGER     NOT NULL,
    drug_code       VARCHAR(80),
    duration_days   NUMERIC(12,2),
    CONSTRAINT fk_med_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE,
    CONSTRAINT fk_med_drug FOREIGN KEY (drug_code)
        REFERENCES drug_reference(drug_code) ON DELETE RESTRICT,
    CONSTRAINT uq_med_participant_row UNIQUE (participant_id, source_row_no)
);

CREATE TABLE IF NOT EXISTS chemical_analyte (
    analyte_code       VARCHAR(80) PRIMARY KEY,
    analyte_label      TEXT        NOT NULL,
    measurement_unit   VARCHAR(60),
    cas_number         VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS chemical_result (
    participant_id   VARCHAR(32)    NOT NULL,
    analyte_code     VARCHAR(80)    NOT NULL,
    measured_value   NUMERIC(20,7),
    PRIMARY KEY (participant_id, analyte_code),
    CONSTRAINT fk_chem_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE,
    CONSTRAINT fk_chem_analyte FOREIGN KEY (analyte_code)
        REFERENCES chemical_analyte(analyte_code) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS chemical_comment (
    participant_id  VARCHAR(32) NOT NULL,
    analyte_code    VARCHAR(80) NOT NULL,
    comment_code    VARCHAR(50),
    PRIMARY KEY (participant_id, analyte_code),
    CONSTRAINT fk_ccom_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE,
    CONSTRAINT fk_ccom_analyte FOREIGN KEY (analyte_code)
        REFERENCES chemical_analyte(analyte_code) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS survey_weight (
    participant_id  VARCHAR(32)   NOT NULL,
    weight_code     VARCHAR(80)   NOT NULL,
    weight_value    NUMERIC(20,8),
    PRIMARY KEY (participant_id, weight_code),
    CONSTRAINT fk_weight_participant FOREIGN KEY (participant_id)
        REFERENCES participant(participant_id) ON DELETE CASCADE
);

COMMIT;
