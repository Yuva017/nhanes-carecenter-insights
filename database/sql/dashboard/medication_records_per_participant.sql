WITH entry_counts AS (
    SELECT participant_id, COUNT(*) AS n
    FROM medication_entry
    GROUP BY participant_id
), participants_by_band AS (
    SELECT LEAST(COALESCE(e.n, 0), 3) AS band, COUNT(*) AS participants
    FROM participant AS p
    LEFT JOIN entry_counts AS e USING (participant_id)
    GROUP BY 1
)
SELECT (ARRAY['No linked entries', '1 entry', '2 entries', '3+ entries'])[band + 1] AS entry_band,
       participants
FROM participants_by_band
ORDER BY band;
