-- Lectures 3, 4, 10. Data changes, routines, Row triggers, and atomicity.
-- All data and catalog objects in this lab are scoped to the database session.
INSERT INTO participant VALUES (105, 11, 29) RETURNING *;
INSERT INTO physiological_profile VALUES (105, 24.2) RETURNING *;
UPDATE participant SET age_years = age_years + 1 WHERE participant_id = 105 RETURNING *;
DELETE FROM participant WHERE participant_id = 105 RETURNING *;
SELECT COUNT(*) AS cascaded_profile_rows
FROM physiological_profile WHERE participant_id = 105;

CREATE FUNCTION pg_temp.medication_count(person integer) RETURNS bigint
LANGUAGE sql STABLE AS $$
    SELECT COUNT(*) FROM pg_temp.medication_entry WHERE participant_id = person
$$;

CREATE FUNCTION pg_temp.medication_summary()
RETURNS TABLE (drug_code text, entry_count bigint)
LANGUAGE sql STABLE AS $$
    SELECT m.drug_code, COUNT(*) FROM pg_temp.medication_entry AS m GROUP BY m.drug_code
$$;

CREATE PROCEDURE pg_temp.correct_participant_age(person integer, new_age integer)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE pg_temp.participant SET age_years = new_age WHERE participant_id = person;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Participant % does not exist', person;
    END IF;
END;
$$;

SELECT pg_temp.medication_count(102);
SELECT * FROM pg_temp.medication_summary() ORDER BY drug_code;
CALL pg_temp.correct_participant_age(104, 62);
SELECT participant_id, age_years FROM participant WHERE participant_id = 104;

CREATE FUNCTION pg_temp.validate_medication() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.drug_code IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM pg_temp.drug_reference AS d WHERE d.drug_code = NEW.drug_code
    ) THEN
        RAISE EXCEPTION 'Unknown drug code %', NEW.drug_code USING ERRCODE = 'P2001';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER validate_medication
BEFORE INSERT OR UPDATE OF drug_code ON medication_entry
FOR EACH ROW EXECUTE FUNCTION pg_temp.validate_medication();

-- Statement-level AFTER trigger. An UPDATE of several rows emits one audit event.
CREATE TEMP TABLE medication_audit (operation text NOT NULL);
CREATE FUNCTION pg_temp.audit_medication_statement() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO pg_temp.medication_audit VALUES (TG_OP);
    RETURN NULL;
END;
$$;
CREATE TRIGGER audit_medication
AFTER INSERT OR UPDATE OR DELETE ON medication_entry
FOR EACH STATEMENT EXECUTE FUNCTION pg_temp.audit_medication_statement();

BEGIN;
UPDATE medication_entry SET duration_days = duration_days + 1 WHERE drug_code = 'A';
INSERT INTO medication_entry (participant_id, source_row_no, drug_code) VALUES (104, 1, 'B');
COMMIT;
SELECT operation, COUNT(*) FROM medication_audit GROUP BY operation ORDER BY operation;

-- SAVEPOINT rollback allows the outer transaction to continue.
BEGIN;
SAVEPOINT before_edit;
UPDATE participant SET age_years = 90 WHERE participant_id = 104;
ROLLBACK TO SAVEPOINT before_edit;
SELECT age_years AS age_after_savepoint_rollback FROM participant WHERE participant_id = 104;
COMMIT;

-- An exception block rolls back its earlier successful write as well as the rejected write.
DO $$
BEGIN
    BEGIN
        UPDATE pg_temp.participant SET age_years = 90 WHERE participant_id = 104;
        INSERT INTO pg_temp.medication_entry (participant_id, source_row_no, drug_code)
        VALUES (104, 2, 'unknown');
        RAISE EXCEPTION 'Expected the trigger to reject the drug';
    EXCEPTION WHEN SQLSTATE 'P2001' THEN
        RAISE NOTICE 'Expected trigger failure: %', SQLERRM;
    END;
END;
$$;
SELECT p.age_years AS age_after_trigger_failure,
       (SELECT COUNT(*) FROM medication_entry
        WHERE participant_id = 104 AND source_row_no = 2) AS rejected_rows,
       (SELECT COUNT(*) FROM medication_audit) AS committed_audit_rows
FROM participant AS p WHERE participant_id = 104;

-- CHECK, UNIQUE and FK failures. Each is caught explicitly so the lab continues.
DO $$
BEGIN
    BEGIN
        UPDATE pg_temp.participant SET age_years = -1 WHERE participant_id = 104;
        RAISE EXCEPTION 'Expected the age CHECK to fail';
    EXCEPTION WHEN check_violation THEN RAISE NOTICE 'Age CHECK rejected -1';
    END;
    BEGIN
        INSERT INTO pg_temp.medication_entry (participant_id, source_row_no)
        VALUES (104, 1);
        RAISE EXCEPTION 'Expected the row key to fail';
    EXCEPTION WHEN unique_violation THEN RAISE NOTICE 'Duplicate event key rejected';
    END;
    BEGIN
        DELETE FROM pg_temp.survey_cycle WHERE cycle_id = 11;
        RAISE EXCEPTION 'Expected ON DELETE RESTRICT to fail';
    EXCEPTION WHEN foreign_key_violation THEN RAISE NOTICE 'Referenced cycle protected';
    END;
END;
$$;
