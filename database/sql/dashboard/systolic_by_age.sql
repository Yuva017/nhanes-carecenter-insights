WITH observations AS (
    SELECT CASE WHEN d.age_years < 20 THEN 1
                WHEN d.age_years < 40 THEN 2
                WHEN d.age_years < 60 THEN 3
                ELSE 4 END AS age_band,
           f.systolic_bp
    FROM demographic_profile AS d
    JOIN physiological_profile AS f USING (participant_id)
    WHERE d.age_years IS NOT NULL AND f.systolic_bp IS NOT NULL
)
SELECT (ARRAY['under 20', '20–39', '40–59', '60+'])[age_band] AS age_group,
       ROUND(AVG(systolic_bp), 1) AS avg_systolic,
       COUNT(*) AS observations
FROM observations
GROUP BY age_band
ORDER BY age_band;
