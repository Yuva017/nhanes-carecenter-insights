# Live PostgreSQL exercises

Use a disposable database and two separate `psql` sessions for the locking exercise.

## Full transaction abort

In one session, run `\i run_validation.sql` from the lab directory first. The lab tables are temporary and belong to this session. At an interactive prompt, run each command individually. The error and the next command's aborted-transaction message are expected.

```sql
BEGIN;
UPDATE participant SET age_years = 90 WHERE participant_id = 104;
INSERT INTO medication_entry (participant_id, source_row_no, drug_code)
VALUES (104, 2, 'missing-code');
SELECT age_years FROM participant WHERE participant_id = 104;
ROLLBACK;
SELECT age_years FROM participant WHERE participant_id = 104;
SELECT COUNT(*) FROM medication_entry WHERE participant_id = 104 AND source_row_no = 2;
```

The final age is 62 and the final count is 0. A row added to an audit table earlier in the aborted transaction would roll back as well.

## Isolation and row-lock blocking

In session A, create a small shared table in the disposable database.

```sql
CREATE TABLE dmql_lab_shared_counter (id integer PRIMARY KEY, value integer NOT NULL);
INSERT INTO dmql_lab_shared_counter VALUES (1, 0);
BEGIN;
UPDATE dmql_lab_shared_counter SET value = value + 1 WHERE id = 1;
```

In session B, check the committed value, then try to update the row held by A.

```sql
SELECT value FROM dmql_lab_shared_counter WHERE id = 1;
BEGIN ISOLATION LEVEL READ COMMITTED;
SET LOCAL lock_timeout = '3s';
UPDATE dmql_lab_shared_counter SET value = value + 1 WHERE id = 1;
ROLLBACK;
```

A plain read in B sees 0 while A's write is pending. B's update times out if A is still open after three seconds. In A, run `COMMIT`. In B, repeat the update in a new transaction and commit. The value should become 2. Drop the practice table after both transactions finish.
