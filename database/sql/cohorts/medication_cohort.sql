-- Compare drug classes within the same loaded, unweighted participant cohort.
CREATE FUNCTION pg_temp.medication_cohort_summary(
    selected_cycle integer, minimum_age integer, maximum_age integer
)
RETURNS TABLE (cohort_size bigint, drug_class text, participants bigint, entries bigint)
LANGUAGE sql STABLE AS $$
    WITH cohort AS MATERIALIZED (
        SELECT p.participant_id
        FROM public.participant AS p
        LEFT JOIN public.demographic_profile AS d USING (participant_id)
        WHERE (selected_cycle IS NULL OR p.cycle_id = selected_cycle)
          AND (minimum_age IS NULL OR d.age_years >= minimum_age)
          AND (maximum_age IS NULL OR d.age_years <= maximum_age)
    ), totals AS (
        SELECT COUNT(*) AS cohort_size FROM cohort
    ), by_class AS (
        SELECT COALESCE(NULLIF(BTRIM(r.drug_class), ''), 'Unclassified') AS drug_class,
               COUNT(DISTINCT c.participant_id) AS participants,
               COUNT(*) AS entries
        FROM cohort AS c
        JOIN public.medication_entry AS m USING (participant_id)
        LEFT JOIN public.drug_reference AS r USING (drug_code)
        GROUP BY 1
    )
    SELECT t.cohort_size, b.drug_class, b.participants, b.entries
    FROM totals AS t LEFT JOIN by_class AS b ON TRUE
$$;
