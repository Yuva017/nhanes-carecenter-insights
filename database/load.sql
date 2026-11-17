-- Bulk load: staging tables -> final relations
-- Staging tables are populated by src/carecenter/etl/load.py via pandas to_sql.
TRUNCATE survey_weight, chemical_comment, chemical_result, medication_entry,
         dietary_entry, survey_cycle, participant, demographic_profile,
         mortality_profile, questionnaire_profile, occupation_profile,
         physiological_profile, drug_reference, chemical_analyte CASCADE;

INSERT INTO survey_cycle (cycle_id, period_label, start_year, end_year)
SELECT DISTINCT cycle_id, cycle_id || '-' || (cycle_id + 1), cycle_id, cycle_id + 1
FROM staging.participant;

INSERT INTO participant (participant_id, source_seqn, cycle_id)
SELECT participant_id, source_seqn, cycle_id FROM staging.participant;

INSERT INTO demographic_profile (participant_id, age_years, sex_code, race_code, poverty_ratio)
SELECT participant_id, age_years, sex_code, race_code, poverty_ratio FROM staging.demographic_profile;

INSERT INTO mortality_profile (participant_id, vital_status, followup_months)
SELECT participant_id, vital_status, followup_months FROM staging.mortality_profile;

INSERT INTO questionnaire_profile (participant_id, smoking_code, diabetes_code)
SELECT participant_id, smoking_code, diabetes_code FROM staging.questionnaire_profile;

INSERT INTO occupation_profile (participant_id, employment_code, hours_worked)
SELECT participant_id, employment_code, hours_worked FROM staging.occupation_profile;

INSERT INTO physiological_profile (participant_id, body_mass_index, systolic_bp)
SELECT participant_id, body_mass_index, systolic_bp FROM staging.physiological_profile;

INSERT INTO dietary_entry (participant_id, source_row_no, dietary_code, amount)
SELECT participant_id, source_row_no, dietary_code, amount FROM staging.dietary_entry;

INSERT INTO drug_reference (drug_code, drug_label, drug_class)
SELECT DISTINCT drug_code, drug_label, drug_class FROM staging.medication_entry
WHERE drug_code IS NOT NULL;

INSERT INTO medication_entry (participant_id, source_row_no, drug_code, duration_days)
SELECT participant_id, source_row_no, drug_code, duration_days FROM staging.medication_entry;

INSERT INTO chemical_analyte (analyte_code, analyte_label, measurement_unit, cas_number)
SELECT DISTINCT analyte_code, analyte_label, measurement_unit, cas_number
FROM staging.chemical_result WHERE analyte_code IS NOT NULL;

INSERT INTO chemical_result (participant_id, analyte_code, measured_value)
SELECT participant_id, analyte_code, measured_value FROM staging.chemical_result;

INSERT INTO chemical_comment (participant_id, analyte_code, comment_code)
SELECT participant_id, analyte_code, comment_code FROM staging.chemical_comment;

INSERT INTO survey_weight (participant_id, weight_code, weight_value)
SELECT participant_id, weight_code, weight_value FROM staging.survey_weight;
