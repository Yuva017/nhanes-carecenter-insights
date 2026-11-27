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

-- Fails validation, leaves the medication row uninserted, and re-raises:
-- SELECT insert_medication_safe('<existing participant>', 1, 'BADCODE999', 30);
