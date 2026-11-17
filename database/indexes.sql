-- Phase 2 Task 7 baseline: indexes proposed before EXPLAIN analysis
-- Foreign-key lookup indexes (Postgres does not auto-index FK child columns)
CREATE INDEX IF NOT EXISTS idx_participant_cycle      ON participant (cycle_id);
CREATE INDEX IF NOT EXISTS idx_diet_participant       ON dietary_entry (participant_id);
CREATE INDEX IF NOT EXISTS idx_med_participant        ON medication_entry (participant_id);
CREATE INDEX IF NOT EXISTS idx_med_drug               ON medication_entry (drug_code);
CREATE INDEX IF NOT EXISTS idx_chem_result_analyte    ON chemical_result (analyte_code);
CREATE INDEX IF NOT EXISTS idx_chem_comment_analyte   ON chemical_comment (analyte_code);
-- Analytics columns
CREATE INDEX IF NOT EXISTS idx_demo_age               ON demographic_profile (age_years);
CREATE INDEX IF NOT EXISTS idx_phys_bmi               ON physiological_profile (body_mass_index);
