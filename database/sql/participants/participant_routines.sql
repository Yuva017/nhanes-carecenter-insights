CREATE OR REPLACE FUNCTION add_participant(
    p_id VARCHAR(32), p_seqn BIGINT, p_cycle INTEGER,
    p_age SMALLINT DEFAULT NULL, p_sex VARCHAR(30) DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO participant (participant_id, source_seqn, cycle_id)
    VALUES (p_id, p_seqn, p_cycle);
    INSERT INTO demographic_profile (participant_id, age_years, sex_code)
    VALUES (p_id, p_age, p_sex);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION participant_summary(p_id VARCHAR(32))
RETURNS TABLE (age_years SMALLINT, n_medications BIGINT, avg_bmi NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT d.age_years,
           (SELECT COUNT(*) FROM medication_entry m WHERE m.participant_id = p_id),
           p.body_mass_index
    FROM demographic_profile d
    LEFT JOIN physiological_profile p ON p.participant_id = d.participant_id
    WHERE d.participant_id = p_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION delete_participant(p_id VARCHAR(32)) RETURNS VOID AS $$
BEGIN
    DELETE FROM participant WHERE participant_id = p_id;
END;
$$ LANGUAGE plpgsql;
