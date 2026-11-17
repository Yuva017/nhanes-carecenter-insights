-- Phase 2 Task 6: transaction with failure handling using a trigger
--
-- Pattern: a BEFORE-trigger validates the insert and raises an exception;
-- a wrapping procedure catches the failure, logs it into transaction_log
-- (the log write happens inside the EXCEPTION block, i.e. after the failed
-- statement's rollback), and re-raises so the caller sees the failure.

CREATE TABLE IF NOT EXISTS transaction_log (
    log_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    operation     VARCHAR(60) NOT NULL,
    error_message TEXT
);

CREATE OR REPLACE FUNCTION trg_medication_validate()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.drug_code IS NOT NULL AND NEW.drug_code NOT IN
       (SELECT drug_code FROM drug_reference) THEN
        RAISE EXCEPTION 'drug_code % not present in drug_reference', NEW.drug_code;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_medication_validate ON medication_entry;
CREATE TRIGGER trg_medication_validate
BEFORE INSERT ON medication_entry
FOR EACH ROW EXECUTE FUNCTION trg_medication_validate();

-- Wrapper transaction with failure handling
CREATE OR REPLACE FUNCTION insert_medication_safe(
    p_participant VARCHAR(32), p_row_no INTEGER,
    p_drug VARCHAR(80), p_days NUMERIC
) RETURNS VOID AS $$
BEGIN
    INSERT INTO medication_entry (participant_id, source_row_no, drug_code, duration_days)
    VALUES (p_participant, p_row_no, p_drug, p_days);
EXCEPTION WHEN others THEN
    INSERT INTO transaction_log (operation, error_message)
    VALUES ('insert_medication_safe(' || p_participant || ')', SQLERRM);
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- Demonstration:
-- SELECT insert_medication_safe('<existing participant>', 1, 'BADCODE999', 30);
--   -> fails the trigger, row NOT inserted, failure logged in transaction_log;
--   -> the transaction aborts and rolls back, so the database state is unchanged.
