-- Phase 2 Task 5: INSERT / UPDATE / DELETE demonstration queries

-- Insert a participant with demographics (transaction demo uses this too)
INSERT INTO participant (participant_id, source_seqn, cycle_id)
VALUES ('TEST0000001', 999999, 2015);

INSERT INTO demographic_profile (participant_id, age_years, sex_code, race_code, poverty_ratio)
VALUES ('TEST0000001', 34, 'male', 'nh_white', 2.5);

-- Update: correct a reported age
UPDATE demographic_profile
SET age_years = 35
WHERE participant_id = 'TEST0000001';

-- Delete: remove the test participant (cascades to profiles)
DELETE FROM participant
WHERE participant_id = 'TEST0000001';
