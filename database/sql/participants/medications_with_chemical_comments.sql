SELECT DISTINCT pt.participant_id, m.drug_code, c.comment_code
FROM participant pt
JOIN medication_entry m ON m.participant_id = pt.participant_id
JOIN chemical_comment c ON c.participant_id = pt.participant_id
WHERE c.comment_code IS NOT NULL
ORDER BY pt.participant_id
LIMIT 50;
