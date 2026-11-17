-- Phase 2 Task 5: SELECT queries (join, group by, order by, subquery)

-- Q1 join + order by: average BMI by age group and cycle (Phase 1 question 1)
SELECT sc.period_label,
       CASE WHEN d.age_years < 20 THEN 'under 20'
            WHEN d.age_years < 40 THEN '20-39'
            WHEN d.age_years < 60 THEN '40-59'
            ELSE '60+' END AS age_group,
       ROUND(AVG(p.body_mass_index), 2) AS avg_bmi
FROM participant pt
JOIN survey_cycle sc      ON sc.cycle_id = pt.cycle_id
JOIN demographic_profile d   ON d.participant_id = pt.participant_id
JOIN physiological_profile p ON p.participant_id = pt.participant_id
WHERE p.body_mass_index IS NOT NULL
GROUP BY sc.period_label, age_group
ORDER BY sc.period_label, age_group;

-- Q2 join: participants reporting medications with below-detection chemical comments
SELECT DISTINCT pt.participant_id, m.drug_code, c.comment_code
FROM participant pt
JOIN medication_entry m  ON m.participant_id = pt.participant_id
JOIN chemical_comment c  ON c.participant_id = pt.participant_id
WHERE c.comment_code IS NOT NULL
ORDER BY pt.participant_id
LIMIT 50;

-- Q3 group by: medication entries per drug class
SELECT dr.drug_class, COUNT(*) AS entry_count
FROM medication_entry m
JOIN drug_reference dr ON dr.drug_code = m.drug_code
GROUP BY dr.drug_class
ORDER BY entry_count DESC;

-- Q4 subquery: participants whose BMI is above the dataset-wide mean
SELECT pt.participant_id, p.body_mass_index
FROM participant pt
JOIN physiological_profile p ON p.participant_id = pt.participant_id
WHERE p.body_mass_index > (
    SELECT AVG(body_mass_index) FROM physiological_profile WHERE body_mass_index IS NOT NULL
)
ORDER BY p.body_mass_index DESC
LIMIT 25;

-- Q5 join + aggregate: dietary intake vs physiological indicators per cycle
SELECT sc.period_label, COUNT(DISTINCT pt.participant_id) AS participants,
       ROUND(AVG(de.amount), 2) AS avg_dietary_amount
FROM participant pt
JOIN survey_cycle sc ON sc.cycle_id = pt.cycle_id
JOIN dietary_entry de ON de.participant_id = pt.participant_id
GROUP BY sc.period_label
ORDER BY sc.period_label;
