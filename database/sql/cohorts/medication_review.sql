-- Review lists belong to this request. Survey records remain read-only.
CREATE TEMP TABLE medication_review_candidates (
    drug_class text PRIMARY KEY, participants bigint NOT NULL, entries bigint NOT NULL
) ON COMMIT DROP;

CREATE TEMP TABLE medication_review_list (
    drug_class text PRIMARY KEY,
    minimum_participants integer NOT NULL CHECK (minimum_participants > 0)
) ON COMMIT DROP;

CREATE FUNCTION pg_temp.enforce_medication_review_threshold() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE participant_total bigint;
BEGIN
    SELECT c.participants INTO participant_total
      FROM pg_temp.medication_review_candidates AS c
     WHERE c.drug_class = NEW.drug_class;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P2002', MESSAGE = 'A selected class is no longer in the cohort. Run the analysis again.';
    END IF;
    IF participant_total < NEW.minimum_participants THEN
        RAISE EXCEPTION USING ERRCODE = 'P2001',
            MESSAGE = NEW.drug_class || ' has ' || participant_total ||
                      ' participants. The review minimum is ' || NEW.minimum_participants || '.';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER medication_review_threshold
BEFORE INSERT ON pg_temp.medication_review_list
FOR EACH ROW EXECUTE FUNCTION pg_temp.enforce_medication_review_threshold();

CREATE PROCEDURE pg_temp.build_medication_review(selected_classes text[], threshold integer)
LANGUAGE sql AS $$
    INSERT INTO pg_temp.medication_review_list (drug_class, minimum_participants)
    SELECT DISTINCT class_name, threshold
    FROM unnest(selected_classes) AS selections(class_name)
$$;
