SELECT dr.drug_class, COUNT(*) AS entry_count
FROM medication_entry m
JOIN drug_reference dr ON dr.drug_code = m.drug_code
GROUP BY dr.drug_class
ORDER BY entry_count DESC;
