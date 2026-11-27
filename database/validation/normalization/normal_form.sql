-- Lectures 5–9. Functional dependencies, closure, decomposition and validation.
-- In the wide row, participant_id -> cycle_id and cycle_id -> period_label.
CREATE TEMP TABLE participant_wide (participant_id integer, age_years integer,
                                    cycle_id integer, period_label text);
INSERT INTO participant_wide VALUES
    (101, 23, 10, '2015–2016'), (102, 45, 10, '2015–2016'),
    (103, NULL, 11, '2017–2018'), (104, 62, 11, '2017–2018');

-- A candidate-key closure exercise. Use a split right-hand side and omit the
-- redundant participant_id -> period_label edge; recursion derives it anyway.
WITH RECURSIVE
fd(lhs, rhs) AS (VALUES ('participant_id', 'cycle_id'),
                        ('participant_id', 'age_years'),
                        ('cycle_id', 'period_label')),
closure(attribute) AS (
    VALUES ('participant_id'::text)
    UNION
    SELECT fd.rhs FROM closure JOIN fd ON fd.lhs = closure.attribute
)
SELECT attribute AS participant_key_closure FROM closure ORDER BY 1;

-- A data check for a proposed FD. Zero observed violations supports checking
-- the import. Constraints and source semantics establish the design dependency.
SELECT cycle_id
FROM participant_wide
GROUP BY cycle_id
HAVING COUNT(DISTINCT period_label) > 1;

-- Verify a sample round-trip in both directions under set semantics.
-- Losslessness follows structurally because shared cycle_id is a key of survey_cycle.
WITH reconstructed AS (
    SELECT p.participant_id, p.age_years, c.cycle_id, c.period_label
    FROM (SELECT DISTINCT participant_id, age_years, cycle_id FROM participant_wide) AS p
    JOIN (SELECT DISTINCT cycle_id, period_label FROM participant_wide) AS c USING (cycle_id)
)
SELECT 'missing' AS discrepancy, d.*
FROM (SELECT * FROM participant_wide EXCEPT SELECT * FROM reconstructed) AS d
UNION ALL
SELECT 'extra', d.*
FROM (SELECT * FROM reconstructed EXCEPT SELECT * FROM participant_wide) AS d;

-- A lossy decomposition under set semantics. Cycle does not determine which
-- age belongs to which participant. Rejoining on cycle fabricates pairings.
WITH ids AS (SELECT DISTINCT participant_id, cycle_id FROM participant_wide),
     ages AS (SELECT DISTINCT cycle_id, age_years FROM participant_wide),
     recombined AS (SELECT participant_id, cycle_id, age_years FROM ids JOIN ages USING (cycle_id))
SELECT * FROM recombined
EXCEPT SELECT participant_id, cycle_id, age_years FROM participant_wide;

-- 3NF synthesis example using two different candidate keys (person, unit)
-- and (person, advisor). advisor -> unit violates BCNF in the ternary relation.
-- The dependent unit is prime, so this particular FD is allowed in 3NF.
CREATE TEMP TABLE advisor_unit (advisor text PRIMARY KEY, unit text NOT NULL);
CREATE TEMP TABLE advising (
    person integer NOT NULL,
    unit text NOT NULL,
    advisor text NOT NULL,
    PRIMARY KEY (person, unit),
    UNIQUE (person, advisor)
);
INSERT INTO advisor_unit VALUES ('a', 'nutrition'), ('b', 'survey');
INSERT INTO advising VALUES (101, 'nutrition', 'a'), (101, 'survey', 'b');
SELECT a.* FROM advising AS a JOIN advisor_unit AS u USING (advisor) WHERE a.unit <> u.unit;
-- A mismatch check is needed while the ternary example repeats the unit.
-- Project the BCNF split and reconstruct it via the advisor key.
SELECT a.person, a.advisor, u.unit
FROM (SELECT DISTINCT person, advisor FROM advising) AS a JOIN advisor_unit AS u USING (advisor);

-- 4NF example. An individual's measured analytes and medication codes can
-- represent independent sets. Joining each set illustrates why storing every
-- cross-product tuple in a single base relation would repeat each fact.
WITH analytes AS (SELECT DISTINCT participant_id, analyte_code FROM chemical_result),
     medications AS (SELECT DISTINCT participant_id, drug_code FROM medication_entry)
SELECT participant_id, analyte_code, drug_code
FROM analytes JOIN medications USING (participant_id)
ORDER BY participant_id, analyte_code, drug_code;
