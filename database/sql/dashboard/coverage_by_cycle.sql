-- One participant per row. Optional measures do not change the cohort denominator.
SELECT sc.period_label,
       COUNT(p.participant_id) AS participants,
       COUNT(f.body_mass_index) AS with_bmi,
       COUNT(f.systolic_bp) AS with_systolic
FROM survey_cycle AS sc
JOIN participant AS p USING (cycle_id)
LEFT JOIN physiological_profile AS f USING (participant_id)
GROUP BY sc.cycle_id, sc.period_label, sc.start_year
ORDER BY sc.start_year, sc.cycle_id;
