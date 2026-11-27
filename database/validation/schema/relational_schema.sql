-- Lectures 1, 2, 5. Isolated synthetic database for learning.
CREATE TEMP TABLE survey_cycle (
    cycle_id integer PRIMARY KEY,
    period_label text NOT NULL UNIQUE
);

CREATE TEMP TABLE participant (
    participant_id integer PRIMARY KEY,
    cycle_id integer NOT NULL REFERENCES survey_cycle ON DELETE RESTRICT,
    age_years integer CHECK (age_years BETWEEN 0 AND 120)
);

CREATE TEMP TABLE physiological_profile (
    participant_id integer PRIMARY KEY REFERENCES participant ON DELETE CASCADE,
    bmi numeric(5,2) CHECK (bmi > 0)
);

CREATE TEMP TABLE drug_reference (
    drug_code text PRIMARY KEY,
    drug_class text NOT NULL
);

CREATE TEMP TABLE medication_entry (
    medication_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    participant_id integer NOT NULL REFERENCES participant ON DELETE CASCADE,
    source_row_no integer NOT NULL CHECK (source_row_no > 0),
    drug_code text REFERENCES drug_reference ON DELETE RESTRICT,
    duration_days integer NOT NULL DEFAULT 1 CHECK (duration_days > 0),
    UNIQUE (participant_id, source_row_no)
);

CREATE TEMP TABLE chemical_analyte (
    analyte_code text PRIMARY KEY,
    unit text NOT NULL
);

CREATE TEMP TABLE chemical_result (
    participant_id integer REFERENCES participant ON DELETE CASCADE,
    analyte_code text REFERENCES chemical_analyte ON DELETE RESTRICT,
    measured_value numeric NOT NULL,
    PRIMARY KEY (participant_id, analyte_code)
);

CREATE TEMP TABLE cohort_rule (
    rule_name text PRIMARY KEY,
    minimum_age integer NOT NULL CHECK (minimum_age >= 0)
);

INSERT INTO survey_cycle VALUES (10, '2015–2016'), (11, '2017–2018');
INSERT INTO participant VALUES (101, 10, 23), (102, 10, 45), (103, 11, NULL), (104, 11, 61);
INSERT INTO physiological_profile VALUES (101, 23.5), (102, 29.1), (103, 26.5);
INSERT INTO drug_reference VALUES ('A', 'Cardiovascular'), ('B', 'Metabolic'), ('C', 'Other');
INSERT INTO medication_entry (participant_id, source_row_no, drug_code, duration_days)
VALUES (101, 1, 'A', 20), (102, 1, 'A', 30), (102, 2, 'B', 15);
INSERT INTO chemical_analyte VALUES ('GLU', 'mg/dL'), ('NA', 'mmol/L');
INSERT INTO chemical_result VALUES (101, 'GLU', 87), (102, 'GLU', 103), (102, 'NA', 137), (103, 'NA', 141);
INSERT INTO cohort_rule VALUES ('adult', 18);

-- Inspect the running database and the physical constraints behind E/R cardinalities.
SELECT current_database(), current_schema();
SELECT conrelid::regclass AS relation, contype AS constraint_type,
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid IN ('pg_temp.participant'::regclass, 'pg_temp.physiological_profile'::regclass,
                   'pg_temp.medication_entry'::regclass, 'pg_temp.chemical_result'::regclass)
ORDER BY conrelid::regclass::text, definition;

-- DDL lifecycle and domain modification.
CREATE TEMP TABLE lifecycle_demo (id integer PRIMARY KEY);
ALTER TABLE lifecycle_demo ADD COLUMN note text DEFAULT 'new' NOT NULL;
INSERT INTO lifecycle_demo (id) VALUES (1);
SELECT * FROM lifecycle_demo;
TRUNCATE TABLE lifecycle_demo;
DROP TABLE lifecycle_demo;

-- A SQL view exposes projection and selection without copying base rows.
CREATE TEMP VIEW known_participant_ages AS
SELECT participant_id, age_years FROM participant WHERE age_years IS NOT NULL;
SELECT * FROM known_participant_ages ORDER BY participant_id;

-- Extended E/R example. Subtype views use one required discriminator so each
-- person belongs to exactly one subtype. Full and partial participation in
-- other relationships are shown by the mandatory participant cycle foreign
-- key and the optional physiological profile.
CREATE TEMP TABLE research_member (
    member_id integer PRIMARY KEY,
    role text NOT NULL CHECK (role IN ('analyst', 'administrator'))
);
CREATE TEMP VIEW analyst AS SELECT member_id FROM research_member WHERE role = 'analyst';
CREATE TEMP VIEW administrator AS
SELECT member_id FROM research_member WHERE role = 'administrator';
INSERT INTO research_member VALUES (1, 'analyst'), (2, 'administrator');
SELECT member_id, 'analyst' AS subtype FROM analyst
UNION ALL SELECT member_id, 'administrator' FROM administrator ORDER BY 1;
