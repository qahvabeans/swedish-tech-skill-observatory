# Swedish Tech Skill Observatory

A local analytics project for tracking technology skill demand in Swedish job ads.

The project currently uses JobTech job ad data, DuckDB, dlt, pandas, dbt, and
Streamlit. Historical data is loaded from local yearly JSONL zip archives,
transformed into skill mention tables, modeled with dbt, and shown in a
Streamlit dashboard.

## Current Pipeline

1. Load live ads from the JobTech historical search API into `main.job_ads`.
2. Load all local historical archives from `data/raw/*.jsonl.zip` into
   `historical_job_ads`.
3. Extract live regex skill lists into `job_skill_lists` and `job_skills`.
4. Extract historical AMS-provided skills into `historical_job_skills` for
   reference and comparison.
5. Extract historical regex-based tech skills into `historical_regex_skills`.
6. Build regex QA tables for manual review of matched terms and example ads.
7. Build dbt models for lineage, regex-primary monthly counts, and dashboard
   trend marts.
8. Explore trends in the Streamlit dashboard.

## Data Layout

- `data/raw/`: yearly JobTech JSONL zip archives.
- `data/temp/`: extracted JSONL files used during local ingestion.
- `data/warehouse/skill_observatory.duckdb`: local DuckDB warehouse.
- `data/exports/`: generated CSV exports.

## Run

Install dependencies with the project environment tooling, then run:

```powershell
python main.py
```

To run individual steps:

```powershell
python -m skill_observatory.ingestion.pipelines.load_historical_ads
python -m skill_observatory.transformations.build_historical_job_skills
python -m skill_observatory.transformations.build_historical_regex_skills
python -m skill_observatory.transformations.build_historical_regex_skill_qa
python -m skill_observatory.transformations.build_monthly_skill_counts
streamlit run src/skill_observatory/dashboard/Home.py
```

To batch-load selected archive years without rebuilding everything:

```powershell
python -m skill_observatory.ingestion.pipelines.load_historical_ads --years 2025
python -m skill_observatory.ingestion.pipelines.load_historical_ads --append --years 2024 2025
```

Without `--append`, the selected archives rebuild `historical_job_ads`. With
`--append`, the selected archive rows are replaced in the existing table.

To build and test the dbt models after Python ingestion and regex extraction:

```powershell
dbt build --profiles-dir .
```

The optional dbt QA summary model expects `historical_regex_skill_matches` to
exist. Enable it after running the Python QA step:

```powershell
dbt build --profiles-dir . --vars "{include_regex_qa: true}"
```

## Docs

- [ARCHITECTURE.md](ARCHITECTURE.md) explains the current system.
- [ROADMAP.md](ROADMAP.md) tracks the planned build-out.
