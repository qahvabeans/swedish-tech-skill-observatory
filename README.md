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

## Run The Pipeline

Activate the virtual environment, then run historical ingestion. To rebuild all
available local archives:

```powershell
python -m skill_observatory.ingestion.pipelines.load_historical_ads --years 2022 2023 2024 2025
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

## Quality Checks

```powershell
ruff check .
python -m compileall main.py src api
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

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) explains the current system design.
- [ROADMAP.md](ROADMAP.md) tracks planned improvements.
