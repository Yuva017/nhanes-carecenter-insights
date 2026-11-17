# CareCenter Insights

Relational database for the NHANES 1988-2018 health and nutrition survey:
Python ETL into PostgreSQL, SQL analytics, and insight dashboards on GitHub Pages.

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
src/analytics/ database queries -> JSON chart data in public/data/
        |
        v
public/                     GitHub Pages site (Chart.js reads public/data/*.json)
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
python -m src.analytics.export  # refresh chart data from PostgreSQL
```

The default pipeline configuration loads the first 25 rows from each source
module for a quick sample. Set `pipeline.max_rows_per_module` to `null` in
`config/config.yaml` to load all rows.

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
