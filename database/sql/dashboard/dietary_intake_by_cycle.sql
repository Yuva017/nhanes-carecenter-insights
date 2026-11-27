SELECT sc.period_label, COUNT(DISTINCT pt.participant_id) AS participants,
       ROUND(AVG(de.amount), 2) AS avg_dietary_amount
FROM participant pt
JOIN survey_cycle sc ON sc.cycle_id = pt.cycle_id
JOIN dietary_entry de ON de.participant_id = pt.participant_id
GROUP BY sc.period_label
ORDER BY sc.period_label;
