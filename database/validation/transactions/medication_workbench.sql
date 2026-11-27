-- Fixed synthetic records for the dashboard operation. The caller rolls back
-- the outer transaction. All writes and routines explicitly target pg_temp.
CREATE TEMP TABLE workbench_case (
    case_id integer PRIMARY KEY,
    status text NOT NULL
) ON COMMIT DROP;

CREATE TEMP TABLE workbench_drug (
    drug_code text PRIMARY KEY
) ON COMMIT DROP;

CREATE TEMP TABLE workbench_medication (
    case_id integer NOT NULL REFERENCES pg_temp.workbench_case,
    drug_code text NOT NULL REFERENCES pg_temp.workbench_drug
) ON COMMIT DROP;

INSERT INTO pg_temp.workbench_case VALUES (1, 'Needs review');
INSERT INTO pg_temp.workbench_drug VALUES ('SAMPLE-RX');

CREATE FUNCTION pg_temp.workbench_medication_count(target_case integer)
RETURNS bigint LANGUAGE sql STABLE AS $$
    SELECT COUNT(*) FROM pg_temp.workbench_medication WHERE case_id = target_case
$$;

CREATE PROCEDURE pg_temp.workbench_record_medication(target_case integer, code text)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE pg_temp.workbench_case SET status = 'Recorded' WHERE case_id = target_case;
    INSERT INTO pg_temp.workbench_medication VALUES (target_case, code);
END;
$$;

CREATE FUNCTION pg_temp.workbench_validate_drug()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_temp.workbench_drug WHERE drug_code = NEW.drug_code) THEN
        RAISE EXCEPTION USING ERRCODE = 'P2001', MESSAGE = 'Drug code is not in the practice formulary';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER workbench_validate_drug
BEFORE INSERT ON pg_temp.workbench_medication
FOR EACH ROW EXECUTE FUNCTION pg_temp.workbench_validate_drug();
