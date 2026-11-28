# CareCenter database validation

This AI-generated study companion uses a small synthetic schema inspired by CareCenter. Use it to practice a SQL operation or a reproducible exercise for each of the 16 lectures. The course syllabus restricts AI-authored project code and reports. Review its disclosure rule before using assistance in graded work.

Run from the project root with PostgreSQL and its `psql` client. The Python
command uses one session and creates temporary tables, views, and routines.

```sh
python -m scripts.validate_database --database carecenter_validation
```

For direct SQL execution, run from this lab directory:

```sh
psql "$DATABASE_URL" -X -f run_validation.sql
```

Use a disposable database for [the two-session locking exercise](manual_transactions.md), which creates a shared table.

The dashboard's **Database validation** section runs the six SQL exercises
below using temporary sample data. Each run uses its own PostgreSQL session
and shows query results and notices. The two-session exercise runs in `psql`
using the linked instructions.

## Lecture map

1. **Introduction.** Inspect the selected database and schema. Observe integrity enforcement and rollback in the later exercises. Start with `schema/relational_schema.sql`.
2. **Relational model.** Create tables with domains, candidate keys, primary keys and foreign keys. Use SQL to demonstrate relational selection, projection, rename, product, joins, union, intersection, and difference. See `schema/relational_schema.sql` and `queries/query_operation.sql`.
3. **Introduction to SQL.** Filter, order, limit, match patterns, handle NULL, aggregate, use `HAVING`, nest queries and run INSERT, UPDATE and DELETE. See `queries/query_operation.sql` and `transactions/routine_and_transaction.sql`.
4. **Intermediate and advanced SQL.** Run inner, natural, theta, left, right and full joins. Call a scalar function, a table-returning function and a procedure. Compare BEFORE row-level validation with AFTER statement-level auditing. See `queries/query_operation.sql` and `transactions/routine_and_transaction.sql`.
5. **E/R modeling.** Inspect the constraints for a mandatory many-to-one cycle, an optional one-to-one profile, one-to-many medication events and a many-to-many participant/analyte relationship. Use subtype views to show total, disjoint specialization. See `schema/relational_schema.sql`.
6. **Relational design I.** Look for violations of a functional dependency with `GROUP BY` and `HAVING`. Rejoin two projections and observe the extra pairings in a lossy decomposition. See `normalization/normal_form.sql`.
7. **Relational design II.** Trace a simple candidate-key closure, see how the split right-hand sides imply an omitted transitive dependency, and check a decomposition by comparing both directions with `EXCEPT`. See `normalization/normal_form.sql`.
8. **BCNF.** Split participant facts from survey cycle descriptions, preserving both direct determinants. Reconstruct the wide sample using the shared cycle key. See `normalization/normal_form.sql`.
9. **3NF and 4NF.** Inspect a ternary advising relation whose non-key determinant is allowed by 3NF. Join independently recorded medication and analyte sets to see the repetition that a single table would introduce. See `normalization/normal_form.sql`.
10. **Transactions.** Commit multiple writes, roll back to a savepoint, and show trigger-induced failure. Run the interactive abort example to see the transaction reject subsequent statements until rollback. See `transactions/routine_and_transaction.sql` and `manual_transactions.md`.
11. **Concurrency control.** Construct a conflict graph from reads and writes and detect a cycle with a recursive query. Inspect read-from and final-writer information for view serializability. See `concurrency/concurrency_control.sql`.
12. **Lock protocols.** Query an event trace for 2PL and strict 2PL violations and find a deadlock in a sample waits-for graph. Observe real row-lock blocking using two sessions. See `concurrency/concurrency_control.sql` and `manual_transactions.md`.
13. **Timestamp control.** Compare basic timestamp ordering and Thomas's write rule on the same read and write attempts using `CASE`. See `concurrency/concurrency_control.sql`.
14. **Indexing.** Inspect primary, secondary, and clustered indexes and compare dense keys with sparse anchors on sorted sample pages. See `performance/index_and_query_plan.sql`.
15. **B-trees.** Run a range query and a composite lookup before and after building B-tree indexes, then insert and remove an indexed row. See `performance/index_and_query_plan.sql`.
16. **Hashing.** Use a PostgreSQL hash index for an equality query. Trace textbook static, extensible and linear bucket-address examples on synthetic keys. See `performance/index_and_query_plan.sql`.

The database runs the index and transaction operations. The textbook schedule checks and bucket traces are SQL teaching examples of the underlying algorithms.

## What to verify in your team’s project

The project handout grades your implementation and evidence. Work from your team's own NHANES dataset, queries, and PostgreSQL instance.

- Execute and capture more than 10 queries, including varied SELECTs, INSERT, UPDATE, DELETE, and calls that demonstrate your stored routines. Your earlier snapshot used a year in place of a survey-cycle key in its mutation demo.
- Show a valid transaction committing, then an invalid input firing a trigger and rolling back an earlier write. Your earlier snapshot attempted to log an error inside the aborted transaction. That log row rolls back too.
- Capture three plans and their costs on your actual loaded data. Compare the same queries with the proposed indexes.
- Record the actual counts for the project’s 14 relations and confirm at least 3,000 total rows. Include the report, database dump, and demo required by the handout.

The automatic examples were exercised with PGlite, an embedded build of PostgreSQL. The test covered the routines, constraint and trigger errors, the full transaction rollback, the schedule checks, and all six before/after plans. The live two-session exercise uses a PostgreSQL server.
