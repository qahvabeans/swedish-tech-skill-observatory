# Architecture

The Swedish Tech Skill Observatory is currently a local-first analytics stack.
The system ingests Swedish job ads, stores them in DuckDB, extracts skill
mentions, aggregates monthly trends, and exposes the results in Streamlit.

## Components

### Ingestion

Live ad ingestion is handled by dlt in
`src/skill_observatory/ingestion/pipelines/load_ads.py`. It fetches a small
sample of ads from the JobTech historical search API and writes them to
`main.job_ads` in DuckDB.

Historical ingestion is handled by
`src/skill_observatory/ingestion/pipelines/load_historical_ads.py`. It discovers
all `*.jsonl.zip` archives in `data/raw`, extracts each archive to `data/temp`,
loads the JSONL records with DuckDB, and creates a combined
`historical_job_ads` table. Each loaded row includes:

- job ad identifiers and publication dates
- monthly publication bucket
- headline and description text
- occupation labels
- AMS `must_have` and `nice_to_have` skill arrays
- `source_archive` and `source_year`

After each archive is loaded, the ingestion step prints row counts, distinct ad
counts, and date ranges.

### Transformations

Skill extraction has two historical sources, but the regex source is the
primary analytical signal:

- `historical_job_skills`: AMS-provided structured skill labels from historical
  job ads. This source is kept for reference and comparison, but it is too noisy
  and broad to drive the main technology trend dashboard.
- `historical_regex_skills`: project-specific technology terms extracted from
  headline and description text.

The shared regex taxonomy lives in
`src/skill_observatory/transformations/skill_extraction.py`. It normalizes skill
aliases into canonical labels such as `python`, `power_bi`, `snowflake`, and
`llm`.

`src/skill_observatory/transformations/build_historical_regex_skill_qa.py`
creates QA tables with matched terms and sample ads for manual review.

`src/skill_observatory/transformations/build_monthly_skill_counts.py` keeps a
combined `all_historical_job_skills` table for lineage and comparison, but the
dashboard-facing `monthly_skill_counts` table is regex-primary. It is aggregated
from `historical_regex_skills` with one row per `publication_month` and `skill`.

### Dashboard

The dashboard is a Streamlit app under `src/skill_observatory/dashboard`.

- `Home.py` provides the entry page.
- `pages/HistoricalSkills.py` reads `monthly_skill_counts`, lets the user select
  a skill, and plots its monthly trend.

### API

The `api` package is currently scaffold only. It is intended as a future FastAPI
layer between DuckDB and the dashboard or external consumers.

### Orchestration

The Dagster package under `src/skill_observatory/orchestration/dagster` is
currently scaffold only. The ingestion and transformation scripts already map
well to future Dagster assets.

## Main Data Flow

```text
data/raw/*.jsonl.zip
        |
        v
historical_job_ads
        |
        +--> historical_job_skills       -- AMS taxonomy skills
        |           |
        |           v
        |   all_historical_job_skills    -- lineage and source comparison
        |
        +--> historical_regex_skills     -- project regex skills
                    |
                    +--> all_historical_job_skills
                    |
                    +--> historical_regex_skill_* -- QA summary and samples
                    |
                    v
        monthly_skill_counts            -- regex-primary dashboard aggregate
                    |
                    v
        Streamlit dashboard
```

Live ads follow a smaller parallel path:

```text
JobTech historical search API
        |
        v
main.job_ads
        |
        v
job_skill_lists
        |
        v
job_skills
```

## Current Limits

- Historical ingestion is local and can require substantial disk space while
  archives are extracted.
- Regex skill coverage is intentionally small and should be expanded.
- Dashboard filtering and comparisons are still minimal.
- FastAPI, Dagster, Docker, tests, and MLflow are not yet implemented.
