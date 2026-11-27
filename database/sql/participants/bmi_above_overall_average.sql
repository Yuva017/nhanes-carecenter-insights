SELECT pt.participant_id, p.body_mass_index
FROM participant pt
JOIN physiological_profile p ON p.participant_id = pt.participant_id
WHERE p.body_mass_index > (
    SELECT AVG(body_mass_index)
    FROM physiological_profile
    WHERE body_mass_index IS NOT NULL
)
ORDER BY p.body_mass_index DESC
LIMIT 25;
