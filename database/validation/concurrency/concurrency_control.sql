-- Lectures 11–13. Analyze schedules with SQL over example operations.
-- These queries analyze teaching examples for protocols. PostgreSQL manages
-- real locks itself. See manual_transactions.md for a live blocking demonstration.

-- Conflict graph: a precedence edge implies an earlier operation from one
-- transaction conflicts with a later operation from a different transaction.
-- A directed cycle means the schedule is not conflict serializable.
WITH RECURSIVE
operations(schedule_name, step, tx, item, kind) AS (
    VALUES ('serial', 1, 't1', 'age', 'R'), ('serial', 2, 't1', 'age', 'W'),
           ('serial', 3, 't2', 'age', 'R'), ('serial', 4, 't2', 'age', 'W'),
           ('cycle', 1, 't1', 'age', 'R'), ('cycle', 2, 't2', 'age', 'R'),
           ('cycle', 3, 't1', 'age', 'W'), ('cycle', 4, 't2', 'age', 'W')
),
edges AS (
    SELECT DISTINCT a.schedule_name, a.tx AS source_tx, b.tx AS target_tx
    FROM operations AS a JOIN operations AS b
      ON a.schedule_name = b.schedule_name AND a.step < b.step
     AND a.tx <> b.tx AND a.item = b.item AND (a.kind = 'W' OR b.kind = 'W')
),
reachable(schedule_name, source_tx, target_tx) AS (
    SELECT schedule_name, source_tx, target_tx FROM edges
    UNION
    SELECT r.schedule_name, r.source_tx, e.target_tx
    FROM reachable AS r JOIN edges AS e
      ON r.schedule_name = e.schedule_name AND r.target_tx = e.source_tx
)
SELECT d.schedule_name,
       NOT EXISTS (SELECT 1 FROM reachable AS r WHERE r.schedule_name = d.schedule_name
                   AND r.source_tx = r.target_tx) AS conflict_serializable
FROM (SELECT DISTINCT schedule_name FROM operations) AS d ORDER BY 1;

-- A read-from/final-writer record for a view-serializability exercise.
WITH writes(step, tx, item) AS (VALUES (1, 't1', 'age'), (3, 't2', 'age'), (4, 't1', 'age')),
     reads(step, tx, item) AS (VALUES (2, 't2', 'age')),
     last_writer AS (
         SELECT DISTINCT ON (item) item, tx FROM writes ORDER BY item, step DESC
     )
SELECT r.tx AS reader, r.item,
       COALESCE((SELECT w.tx FROM writes AS w WHERE w.item = r.item AND w.step < r.step
                 ORDER BY w.step DESC LIMIT 1), 'initial') AS reads_from,
       lw.tx AS final_writer
FROM reads AS r JOIN last_writer AS lw USING (item);

-- 2PL: an acquire after a release violates the shrinking phase.
-- An X-lock release before commit also violates strict 2PL.
WITH events(tx, step, action) AS (
    VALUES ('t1', 1, 'lock'), ('t1', 3, 'commit'), ('t1', 4, 'unlock'),
           ('t2', 2, 'lock'), ('t2', 5, 'unlock'), ('t2', 6, 'lock'), ('t2', 8, 'commit')
)
SELECT tx,
       MAX(step) FILTER (WHERE action = 'lock') < MIN(step) FILTER (WHERE action = 'unlock')
           AS follows_two_phase_locking,
       MIN(step) FILTER (WHERE action = 'unlock') >= MIN(step) FILTER (WHERE action = 'commit')
           AS holds_exclusive_locks_to_commit
FROM events GROUP BY tx ORDER BY tx;

-- A waits-for cycle detects a deadlock in a sample graph.
WITH RECURSIVE waits(waiter, holder) AS (VALUES ('t1', 't2'), ('t2', 't1'), ('t3', 't2')),
reach(waiter, holder) AS (
    SELECT waiter, holder FROM waits
    UNION
    SELECT r.waiter, w.holder FROM reach AS r JOIN waits AS w ON r.holder = w.waiter
)
SELECT waiter AS deadlocked_transaction FROM reach WHERE waiter = holder ORDER BY waiter;

-- Timestamp ordering and Thomas's write rule on example record timestamps.
WITH attempt(label, operation, tx_ts, item_read_ts, item_write_ts) AS (
    VALUES ('outdated read', 'read', 2, 1, 3),
           ('obsolete write', 'write', 2, 1, 3),
           ('write after newer read', 'write', 2, 4, 1),
           ('current write', 'write', 5, 4, 3)
)
SELECT label,
       CASE WHEN operation = 'read' AND tx_ts < item_write_ts THEN 'abort'
            WHEN operation = 'write' AND tx_ts < GREATEST(item_read_ts, item_write_ts) THEN 'abort'
            ELSE 'allow' END AS basic_timestamp_ordering,
       CASE WHEN operation = 'read' AND tx_ts < item_write_ts THEN 'abort'
            WHEN operation = 'write' AND tx_ts < item_read_ts THEN 'abort'
            WHEN operation = 'write' AND tx_ts < item_write_ts THEN 'ignore obsolete write'
            ELSE 'allow' END AS thomas_write_rule
FROM attempt ORDER BY label;
