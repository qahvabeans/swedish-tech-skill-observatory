# Swedish Tech Skill Observatory

A local data engineering and analytics project for tracking technology skill
demand in Swedish job ads.

The project ingests historical Swedish job ad archives from Platsbanken-related
open data, stores them in DuckDB, extracts technology skills with a regex
taxonomy, models dashboard-ready marts with dbt, validates data quality with dbt
tests, and exposes the results in a Streamlit dashboard.

## Why This Project Exists

Job ads contain useful signals about changing technology demand, but the raw
data is nested, large, and not immediately dashboard-friendly. This project
turns local historical archives into reproducible analytical tables for trend,
growth, QA, and geographic analysis.

## Current Stack

- Python for ingestion and regex skill extraction orchestration
- DuckDB as the local analytical warehouse
- dbt-duckdb for staging, marts, and data tests
- MinIO as the local S3-compatible object-storage foundation
- Streamlit for the dashboard
- dlt for the small live-ingestion sample
- ruff for Python linting

## Pipeline

1. Load local historical archives from `data/raw/*.jsonl.zip` into
   `historical_job_ads`.
2. Extract AMS-provided skills into `historical_job_skills` for reference.
3. Extract regex-primary technology skills into:
   - `historical_regex_skill_matches`
   - `historical_regex_skills`
4. Build regex QA tables:
   - `historical_regex_skill_qa_summary`
   - `historical_regex_skill_samples`
5. Build dbt models:
   - `stg_historical_job_ads`
   - `int_all_historical_job_skills`
   - `monthly_skill_counts`
   - `mart_dashboard_skill_trends`
   - `mart_skill_geography`
6. Explore trends, growth, Top N skills, and geography in Streamlit.

## Data Layout

- `data/raw/`: local yearly JSONL zip archives with historical job ads.
- `data/temp/`: temporary extraction area used during ingestion.
- `data/warehouse/skill_observatory.duckdb`: local DuckDB warehouse.
- `data/exports/`: generated CSV exports.

Raw data and the DuckDB warehouse are intentionally not committed.

## Local Object Storage

MinIO runs locally through Docker Compose. It creates the
`skill-observatory` bucket automatically and exposes:

- S3 endpoint: `http://localhost:9000`
- management console: `http://localhost:9001`

Create a local environment file and start it:

```powershell
Copy-Item .env.example .env
docker compose up -d
```

Replace the example password in `.env` before use. The current historical
ingestion can write to both DuckDB and MinIO, while Dagster uses MinIO Bronze as
the default upstream source for dbt.

### MinIO Login And Local Account

Open `http://localhost:9001` and sign in with `MINIO_ROOT_USER` and
`MINIO_ROOT_PASSWORD` from your local `.env`. No account or bucket needs to be
created in the web interface: the `minio-init` container creates the private
`skill-observatory` bucket automatically.

For this local project, keep `S3_ACCESS_KEY` equal to `MINIO_ROOT_USER` and
`S3_SECRET_KEY` equal to `MINIO_ROOT_PASSWORD`. Python, DuckDB, dbt, and Dagster
then use the same local credentials. `.env` is ignored by Git; only the safe
template `.env.example` is committed.

Useful commands:

```powershell
docker compose up -d
docker compose ps
docker compose logs minio-init
docker compose down
```

`docker compose down` keeps the local data volume. Adding `-v` deletes the
MinIO volume and all locally stored Parquet files.

Run the storage tests:

```powershell
python -m pytest tests/storage -m "not integration"
$env:RUN_MINIO_INTEGRATION_TESTS = "1"
python -m pytest tests/storage/test_minio_integration.py
```

Export or replace selected Bronze partitions from the existing DuckDB table:

```powershell
python -m skill_observatory.storage.export_historical_ads --years 2022 2023 2024 2025
```

Build dbt models directly from MinIO and validate parity against the local
source:

```powershell
python -m skill_observatory.transformations.run_dbt
python -m skill_observatory.transformations.validate_minio_parity
```

## Run The Pipeline

Activate the virtual environment, then run historical ingestion. To rebuild all
available local archives:

```powershell
python -m skill_observatory.ingestion.pipelines.load_historical_ads --years 2022 2023 2024 2025
```

To replace selected archive rows and synchronize their Bronze partitions in
the same command:

```powershell
python -m skill_observatory.ingestion.pipelines.load_historical_ads --append --sync-minio --years 2025
```

To run year-by-year and replace only selected archive rows after the first
rebuild:

```powershell
python -m skill_observatory.ingestion.pipelines.load_historical_ads --years 2025
python -m skill_observatory.ingestion.pipelines.load_historical_ads --append --years 2024
python -m skill_observatory.ingestion.pipelines.load_historical_ads --append --years 2023
python -m skill_observatory.ingestion.pipelines.load_historical_ads --append --years 2022
```

Then build skills and marts:

```powershell
python -m skill_observatory.transformations.build_historical_job_skills
python -m skill_observatory.transformations.build_historical_regex_skills
python -m skill_observatory.transformations.build_historical_regex_skill_qa
dbt build --profiles-dir .
```

Run the dashboard:

```powershell
python -m streamlit run src/skill_observatory/dashboard/Home.py
```

## Dagster Orchestration

Start the local Dagster UI:

```powershell
dagster dev -m skill_observatory.orchestration.dagster.definitions
```

Open `http://localhost:3000` and launch `historical_pipeline_job`. Its default
configuration refreshes 2025, validates the corresponding Bronze partition,
reuses existing regex/QA tables, and builds dbt marts from MinIO.

A regex or QA rebuild is intentionally explicit because a full historical
regex rebuild is CPU- and memory-intensive:

```yaml
ops:
  historical_ads_ingestion:
    config:
      years: [2025]
      append: true
  regex_skill_mentions:
    config:
      rebuild: true
  regex_skill_quality:
    config:
      rebuild: true
```

The monthly schedule is included but stopped by default for local development.

## Quality Checks

```powershell
ruff check .
python -m compileall main.py src api
python -m pytest tests/storage -m "not integration"
dbt build --profiles-dir .
```

Current dbt tests cover source null checks, accepted skill-source values,
non-empty monthly skill counts, share bounds, and geographic mart consistency.

## Dashboard

The Streamlit dashboard currently supports:

- raw mentions and normalized share of ads
- multiple skill comparison
- date-range filtering
- Top N skills by month
- fastest growing and declining skills
- geography view by municipality
- detail table for inspection

## Archived Microsoft Fabric Proof Of Concept

The repository retains a completed Microsoft Fabric proof of concept as a
portfolio artifact. It maps the local data product to a Lakehouse with bronze,
silver, and gold layers, but it is not part of the active runtime architecture
and requires no Azure or Fabric subscription.

Export Fabric-ready Parquet files:

```powershell
python -m skill_observatory.fabric.export_fabric_tables
```

See [fabric/README.md](fabric/README.md) for the archived workspace layout,
notebook templates, pipeline definition, and local export helper.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) explains the current system design.
- [ROADMAP.md](ROADMAP.md) tracks planned improvements.
- [fabric/README.md](fabric/README.md) describes the archived Fabric proof of
  concept.
