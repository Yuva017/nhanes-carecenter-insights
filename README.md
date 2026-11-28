# CareCenter Insights

Relational database for the NHANES 1988-2018 health and nutrition survey:
Python ETL into PostgreSQL, SQL analytics, and a live dashboard powered by FastAPI on Render.

## Architecture (layered)

```text
data/raw/*.csv            NHANES source CSVs (Kaggle), never committed
        |
        v
src/jobs/       extract -> transform -> load (pandas + SQLAlchemy)
        |
        v
PostgreSQL (14 relations) schema in database/create.sql, bulk load in database/load.sql
        |
        v
src/api.py                  PostgreSQL aggregates over /api/charts/{dataset}
        |
        v
public/                     Chart.js dashboard (Render or GitHub Pages)
```

## Layers

1. **Extract** (`etl/extract.py`): reads each NHANES CSV module into pandas DataFrames.
2. **Transform** (`etl/transform.py`): harmonizes identifiers (SEQN_new), pivots wide
   chemical/weight columns into long records, maps dictionary codes, preserves NULLs.
3. **Load** (`etl/load.py`): stages raw rows, then executes `sql/load.sql` to populate
   the 14 final relations with keys and constraints enforced.
4. **Database** (`sql/create.sql`): 14 relations in BCNF with PK/FK rules per the
   Phase 1 report (RESTRICT on reference tables, CASCADE on participant children).
5. **Analytics** (`src/analytics/export.py`): runs analytics queries against
   PostgreSQL and exports JSON files into `public/data/`.
6. **Presentation** (`public/index.html`, `public/scripts/dashboard.js`,
   `public/styles/`): interactive Chart.js dashboard with separate behavior and
   stylesheets.

## Quick start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set DATABASE_URL
export DATABASE_URL="$(sed -n 's/^DATABASE_URL=//p' .env)"
psql "$DATABASE_URL" -f database/create.sql
python -m scripts.run_pipeline  # ETL
python -m scripts.check_counts  # row counts per relation
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000  # serve the live dashboard
```

The default pipeline configuration reads up to 25 rows per source module
for a quick sample. To load the available records for all 11 supported
survey periods, run:

```bash
python -m scripts.run_pipeline --full
python -m scripts.check_counts
```

`--full` removes both row caps and includes NHANES III (code `-1`) and
the 10 continuous cycles (codes `1` through `10`). The project's field and
analyte selections still apply.
The loader reads the NHANES CSV files in `data/raw/` and replaces the
normalized CareCenter tables in the PostgreSQL database set by
`DATABASE_URL`. Use the intended database. The import does not create an
Excel workbook.

## SQL layout and Python entry points

- `database/create.sql` creates the application tables. The Python ETL in
  `src/jobs/load.py` executes `database/load.sql` after staging the source data.
- `database/sql/dashboard/` contains one query per dashboard export, loaded by
  `python -m src.analytics.export`.
- `database/sql/participants/` contains participant lookups, CRUD examples,
  and participant routines. `database/sql/medications/` contains the validated
  medication insert operation and its trigger.
- `database/indexes.sql` contains candidate application indexes.
- `database/validation/` groups SQL checks by schema, query, transaction,
  normalization, concurrency, and performance operations. The
  `run_validation.sql` entry point includes them in one PostgreSQL session;
  `src/database_validation.py` runs it using synthetic data and temporary tables.

Run the SQL checks from the project root using a separate database:

```bash
createdb carecenter_validation
python -m scripts.validate_database --database carecenter_validation
```

Set `PGHOST`, `PGPORT`, and `PGUSER` if needed. For authentication, configure
a PostgreSQL password file or a libpq service with `PGSERVICE`. The runner uses
the explicitly named practice database. To capture commands and results in a
file, append `> database_validation.log 2>&1`. See the
[validation guide](database/validation/README.md) and the
[two-session exercise](database/validation/manual_transactions.md).

## Live dashboard and database operations

Run the web backend against your loaded CareCenter PostgreSQL database:

```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port "${PORT:-8000}"
```

The dashboard requests `GET /api/charts/{dataset}`. The Render backend
runs the corresponding SQL under `database/sql/dashboard/` against
PostgreSQL and sends the results as JSON. Chart values describe the loaded
records and are unweighted. On Render and during local development, the
dashboard uses the same origin as the API. The project’s GitHub Pages
deployment calls the Render API from its allowed origin.

The collapsible **SQL activity** pane groups server-captured statements by
dashboard request. It includes failed statements and rollbacks from the
medication review. Entries are kept in the current page,
and bound parameter values are excluded. The dashboard requests the trace
with `?include_sql=true`; regular API responses keep their existing shape.

Use `python -m src.analytics.export` to create optional JSON snapshots.
The live dashboard does not read the exported files.

The medication cohort explorer reads loaded NHANES aggregates by survey period
and age group. Select up to 12 drug classes to prepare a downloadable review
list. A PostgreSQL function calculates counts, a stored procedure assembles
the list, and a trigger rejects the entire list if a selected class is below
the configured minimum participant count. The database user needs permission
to create temporary tables. The lists live only in the request, and the
dashboard's SQL activity pane shows the submitted statements and rollbacks.

Open **Database validation** from the dashboard header, select an exercise,
and click **Run exercise**. The backend runs the corresponding existing file
under `database/validation/` in a dedicated PostgreSQL session. You can expand
the returned tables and messages and inspect the executed SQL in the activity
pane. The exercises use temporary sample data and require the database's
temporary-table privilege.

## GitHub Actions

Add `DATABASE_URL` as a repository Actions secret. Add `KAGGLE_API_TOKEN` too
if Kaggle requires authentication to download the dataset.

Both workflows are manually triggered from the Actions tab:

1. **Load NHANES database** downloads the Kaggle CSV files and loads the
   configured sample into PostgreSQL. The loader replaces the normalized table
   contents, so use the intended database URL.
2. **Refresh dashboard data** runs the aggregate queries, validates the JSON
   files, and deploys the updated `public/` directory to GitHub Pages.

The database must allow connections from GitHub-hosted runners. Configure
network access using your database provider's recommended allowlisting or
network integration.

## License

MIT for the code. NHANES data belongs to its original providers (NCHS / Kaggle).
