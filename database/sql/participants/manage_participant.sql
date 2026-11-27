-- Create a participant and demographic profile.
INSERT INTO participant (participant_id, source_seqn, cycle_id)
VALUES ('TEST0000001', 999999, 2015);

INSERT INTO demographic_profile (participant_id, age_years, sex_code, race_code, poverty_ratio)
VALUES ('TEST0000001', 34, 'male', 'nh_white', 2.5);

-- Update a reported age.
UPDATE demographic_profile
SET age_years = 35
WHERE participant_id = 'TEST0000001';

-- Remove a participant and its dependent profiles.
DELETE FROM participant
WHERE participant_id = 'TEST0000001';
