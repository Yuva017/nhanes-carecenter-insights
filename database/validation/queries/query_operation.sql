-- Lectures 2–4. Relational algebra and SQL query forms.
-- Q01 | Projection, selection, rename, arithmetic, BETWEEN, IN, ORDER BY, LIMIT.
SELECT p.participant_id AS id, p.age_years + 1 AS age_next_year
FROM participant AS p
WHERE p.age_years BETWEEN 20 AND 65 AND p.cycle_id IN (10, 11)
ORDER BY age_next_year DESC, id LIMIT 3;

-- Q02 | String patterns, DISTINCT and explicit NULL handling.
SELECT DISTINCT d.drug_class
FROM drug_reference AS d WHERE d.drug_class LIKE 'Cardio%';
SELECT participant_id, COALESCE(age_years::text, 'Unknown') AS reported_age
FROM participant WHERE age_years IS NULL;

-- Q03 | Cartesian product and a theta join.
SELECT c.cycle_id, a.analyte_code
FROM survey_cycle AS c CROSS JOIN chemical_analyte AS a ORDER BY 1, 2;
SELECT p.participant_id, r.rule_name
FROM participant AS p JOIN cohort_rule AS r ON p.age_years >= r.minimum_age ORDER BY 1;

-- Q04 | Equijoin ON, USING, and NATURAL JOIN over explicitly scoped columns.
SELECT p.participant_id, m.medication_id
FROM participant AS p INNER JOIN medication_entry AS m ON m.participant_id = p.participant_id
ORDER BY 1, 2;
SELECT participant_id, bmi FROM participant JOIN physiological_profile USING (participant_id) ORDER BY 1;
SELECT participant_id, bmi FROM (SELECT participant_id FROM participant) AS p
NATURAL JOIN (SELECT participant_id, bmi FROM physiological_profile) AS f ORDER BY 1;

-- Q05 | LEFT, RIGHT, FULL and unmatched rows.
SELECT p.participant_id, f.bmi
FROM participant AS p LEFT JOIN physiological_profile AS f USING (participant_id) ORDER BY 1;
SELECT d.drug_code, m.medication_id
FROM medication_entry AS m RIGHT JOIN drug_reference AS d USING (drug_code) ORDER BY 1, 2;
WITH bmi_ids AS (SELECT participant_id FROM physiological_profile),
     med_ids AS (SELECT DISTINCT participant_id FROM medication_entry)
SELECT participant_id, b.participant_id IS NOT NULL AS has_bmi,
       m.participant_id IS NOT NULL AS has_med
FROM bmi_ids AS b FULL OUTER JOIN med_ids AS m USING (participant_id) ORDER BY 1;

-- Q06 | Set union, bag union, intersection, and difference.
SELECT participant_id FROM physiological_profile
UNION SELECT participant_id FROM medication_entry ORDER BY 1;
SELECT participant_id FROM physiological_profile
UNION ALL SELECT participant_id FROM medication_entry ORDER BY 1;
SELECT participant_id FROM physiological_profile
INTERSECT SELECT participant_id FROM medication_entry ORDER BY 1;
SELECT participant_id FROM participant
EXCEPT SELECT participant_id FROM physiological_profile ORDER BY 1;

-- Q07 | Grouping, aggregate functions, HAVING, and NULL-sensitive counts.
SELECT cycle_id, COUNT(*) AS participants, COUNT(age_years) AS ages_observed,
       MIN(age_years) AS youngest, MAX(age_years) AS oldest,
       SUM(age_years) AS sum_of_known_ages, ROUND(AVG(age_years), 1) AS mean_age
FROM participant GROUP BY cycle_id HAVING COUNT(*) >= 2 ORDER BY cycle_id;

-- Q08 | A scalar subquery and a correlated anti-join.
SELECT participant_id, bmi FROM physiological_profile
WHERE bmi > (SELECT AVG(bmi) FROM physiological_profile) ORDER BY bmi DESC;
SELECT p.participant_id FROM participant AS p
WHERE NOT EXISTS (SELECT 1 FROM physiological_profile AS f WHERE f.participant_id = p.participant_id)
ORDER BY 1;

-- Q09 | Set membership, quantified comparison and derived table.
SELECT participant_id FROM participant
WHERE participant_id IN (SELECT participant_id FROM medication_entry) ORDER BY 1;
SELECT participant_id, bmi FROM physiological_profile
WHERE bmi >= ALL (SELECT bmi FROM physiological_profile WHERE bmi IS NOT NULL);
SELECT per_drug.drug_code, per_drug.entries
FROM (SELECT drug_code, COUNT(*) AS entries FROM medication_entry GROUP BY drug_code) AS per_drug
WHERE per_drug.entries >= 2;
