SELECT sc.period_label,
       CASE WHEN d.age_years < 20 THEN 'under 20'
            WHEN d.age_years < 40 THEN '20-39'
            WHEN d.age_years < 60 THEN '40-59'
            ELSE '60+' END AS age_group,
       ROUND(AVG(p.body_mass_index), 2) AS avg_bmi
FROM participant pt
JOIN survey_cycle sc ON sc.cycle_id = pt.cycle_id
JOIN demographic_profile d ON d.participant_id = pt.participant_id
JOIN physiological_profile p ON p.participant_id = pt.participant_id
WHERE p.body_mass_index IS NOT NULL
GROUP BY sc.period_label, age_group
ORDER BY sc.period_label, age_group;
