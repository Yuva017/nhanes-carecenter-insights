-- Lectures 14–16. PostgreSQL indexes tested on synthetic data.
-- Each query runs before and after its index on the same dataset.
BEGIN;
-- Use normal scan choices even when the host session changed planner settings.
SET LOCAL enable_seqscan = on;
SET LOCAL enable_indexscan = on;
SET LOCAL enable_bitmapscan = on;

CREATE TEMP TABLE index_demo (
    event_id integer PRIMARY KEY,
    participant_id integer NOT NULL,
    cycle_id integer NOT NULL,
    drug_code text NOT NULL,
    duration_days integer NOT NULL,
    detail text NOT NULL
);

INSERT INTO index_demo
SELECT n, n % 8191, n % 11 + 1, 'drug-' || (n % 999), (n * 17) % 10000,
       repeat('synthetic event ', 5)
FROM generate_series(1, 50000) AS n;
ANALYZE index_demo;

-- 1. Ordered bounded range using a B-tree.
EXPLAIN (ANALYZE, BUFFERS)
SELECT event_id, duration_days FROM index_demo
WHERE duration_days BETWEEN 6010 AND 6016 ORDER BY duration_days;
CREATE INDEX index_demo_duration ON index_demo USING btree (duration_days);
EXPLAIN (ANALYZE, BUFFERS)
SELECT event_id, duration_days FROM index_demo
WHERE duration_days BETWEEN 6010 AND 6016 ORDER BY duration_days;

-- 2. Equality lookup using a secondary hash index.
EXPLAIN (ANALYZE, BUFFERS)
SELECT event_id, drug_code FROM index_demo WHERE drug_code = 'drug-42';
CREATE INDEX index_demo_drug ON index_demo USING hash (drug_code);
EXPLAIN (ANALYZE, BUFFERS)
SELECT event_id, drug_code FROM index_demo WHERE drug_code = 'drug-42';

-- 3. Multi-column predicate using a composite B-tree.
EXPLAIN (ANALYZE, BUFFERS)
SELECT event_id, duration_days FROM index_demo WHERE cycle_id = 10 AND participant_id = 42;
CREATE INDEX index_demo_cycle_person ON index_demo USING btree (cycle_id, participant_id);
EXPLAIN (ANALYZE, BUFFERS)
SELECT event_id, duration_days FROM index_demo WHERE cycle_id = 10 AND participant_id = 42;

-- Inspect supported access methods and the difference between primary and secondary indexes.
SELECT c.relname AS index_name, a.amname AS access_method, i.indisprimary AS primary_index,
       i.indisclustered AS used_for_cluster
FROM pg_index AS i JOIN pg_class AS c ON c.oid = i.indexrelid
JOIN pg_am AS a ON a.oid = c.relam
WHERE i.indrelid = 'pg_temp.index_demo'::regclass ORDER BY c.relname;

-- Physical clustering changes heap order once. An explicit ORDER BY still
-- controls output order. PostgreSQL does not maintain CLUSTER order on inserts.
CLUSTER index_demo USING index_demo_duration;
ANALYZE index_demo;
SELECT event_id, duration_days FROM index_demo ORDER BY duration_days, event_id LIMIT 5;

-- Textbook dense index vs. one sparse anchor per synthetic sorted page.
WITH ordered AS (
    SELECT n AS search_key, (n - 1) / 3 AS page_no FROM generate_series(1, 12) AS n
)
SELECT page_no, ARRAY_AGG(search_key ORDER BY search_key) AS dense_keys,
       MIN(search_key) AS sparse_anchor
FROM ordered GROUP BY page_no ORDER BY page_no;

-- Trace three textbook bucket-address rules on the same teaching keys.
-- The extensible directory has global depth 2. The linear table is splitting
-- bucket 0 from a two-bucket round, so only that bucket uses the next hash.
WITH directory(dir_slot, bucket) AS (VALUES (0, 0), (1, 1), (2, 2), (3, 1))
SELECT key, key % 2 AS static_bucket, d.bucket AS extensible_bucket,
       CASE WHEN key % 2 < 1 THEN key % 4 ELSE key % 2 END AS linear_bucket
FROM generate_series(0, 7) AS key JOIN directory AS d ON d.dir_slot = key % 4
ORDER BY key;

-- Point lookup and maintenance of the indexed entries.
INSERT INTO index_demo VALUES (50001, 90000, 1, 'drug-lab', 6012, 'new synthetic event');
SELECT event_id FROM index_demo WHERE drug_code = 'drug-lab';
DELETE FROM index_demo WHERE event_id = 50001;
SELECT COUNT(*) AS remaining_indexed_rows FROM index_demo WHERE drug_code = 'drug-lab';
COMMIT;
