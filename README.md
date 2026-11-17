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
src/insights/  analytics queries -> JSON exports for charts
        |
        v
public/                     GitHub Pages site (Chart.js reads docs/data/*.json)
```

## Layers

1. **Extract** (`etl/extract.py`): reads each NHANES CSV module into pandas DataFrames.
2. **Transform** (`etl/transform.py`): harmonizes identifiers (SEQN_new), pivots wide
   chemical/weight columns into long records, maps dictionary codes, preserves NULLs.
3. **Load** (`etl/load.py`): stages raw rows, then executes `sql/load.sql` to populate
   the 14 final relations with keys and constraints enforced.
4. **Database** (`sql/create.sql`): 14 relations in BCNF with PK/FK rules per the
   Phase 1 report (RESTRICT on reference tables, CASCADE on participant children).
5. **Insights** (`insights/export.py`): runs the analytics queries in
   `sql/queries/`, exports small JSON files into `docs/data/`.
6. **Presentation** (`docs/index.html`): static GitHub Pages dashboard.

## Quick start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set DATABASE_URL
export DATABASE_URL="$(sed -n 's/^DATABASE_URL=//p' .env)"
psql "$DATABASE_URL" -f database/create.sql
python scripts/run_pipeline.py  # ETL
python scripts/check_counts.py  # row counts per relation
python src/carecenter/insights/export.py
```

## License

MIT for the code. NHANES data belongs to its original providers (NCHS / Kaggle).
