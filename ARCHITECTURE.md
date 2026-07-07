# Architecture

Swedish Tech Skill Observatory is a local-first data engineering project. It
turns historical Swedish job ad archives into analytical DuckDB tables, dbt
marts, and a Streamlit dashboard for technology skill demand.

## High-Level Flow

```text
data/raw/*.jsonl.zip
        |
        v
historical_job_ads                         -- Python + DuckDB ingestion
        |
        +--> historical_job_skills          -- AMS skills, reference only
        |
        +--> historical_regex_skill_matches -- DuckDB-native regex extraction
                    |
                    +--> historical_regex_skills
                    |
                    +--> historical_regex_skill_qa_summary
                    |
                    +--> historical_regex_skill_samples
                    |
                    v
dbt models
        |
        +--> stg_historical_job_ads
        +--> int_all_historical_job_skills
        +--> monthly_skill_counts
        +--> mart_dashboard_skill_trends
        +--> mart_skill_geography
                    |
                    v
Streamlit dashboard
```

## Ingestion

Historical ingestion lives in
`src/skill_observatory/ingestion/pipelines/load_historical_ads.py`.

It:

- discovers local `*.jsonl.zip` archives in `data/raw`
- supports selected years with `--years`
- supports idempotent archive replacement with `--append`
- handles schema differences between 2022 and later archives
- extracts useful job, occupation, skill, and geography fields
- writes to `historical_job_ads` in DuckDB
- prints per-archive row counts, distinct ads, and date ranges

The historical table includes:

- job id and publication dates
- headline and description text
- occupation labels
- AMS `must_have` and `nice_to_have` skill arrays
- municipality, region, postcode, city, longitude, latitude
- source archive and source year

Live/sample ingestion exists separately through dlt in
`src/skill_observatory/ingestion/pipelines/load_ads.py`.

## Skill Extraction

The primary analytical signal is regex-based technology extraction.

`src/skill_observatory/transformations/skill_extraction.py` defines the skill
taxonomy and aliases.

`src/skill_observatory/transformations/build_historical_regex_skills.py` runs
regex matching inside DuckDB instead of loading all ad text into pandas. It
creates:

- `historical_regex_skill_matches`: one row per ad and matched skill, including
  matched surface text and text snippets for QA.
- `historical_regex_skills`: compact one-row-per-ad-skill table used by dbt.

AMS skills are retained in `historical_job_skills`, but they are treated as a
secondary comparison/reference source because many AMS classes are not useful
technology skills.

## Quality Assurance

`src/skill_observatory/transformations/build_historical_regex_skill_qa.py`
builds QA tables from `historical_regex_skill_matches`:

- `historical_regex_skill_qa_summary`
- `historical_regex_skill_samples`

These tables are meant for reviewing false positives, alias quality, and missing
coverage in the regex taxonomy.

## dbt Modeling

The dbt project lives under `dbt/` and uses `profiles.yml` to connect to the
local DuckDB warehouse.

Current dbt models:

- `stg_historical_job_ads`: staging view for historical ads and geography.
- `int_all_historical_job_skills`: lineage table combining AMS and regex
  sources.
- `monthly_skill_counts`: regex-primary monthly skill mentions.
- `mart_dashboard_skill_trends`: mentions plus normalized share of ads.
- `mart_skill_geography`: skill demand by month and municipality.

dbt tests validate source nulls, accepted skill source values, non-empty trend
tables, share bounds, and geography consistency.

## Dashboard

The dashboard is a Streamlit app under `src/skill_observatory/dashboard`.

`pages/HistoricalSkills.py` reads dbt marts and currently supports:

- skill trend comparison
- mentions vs share of ads
- Top N by selected month
- fastest growing and declining skills
- geography view by municipality
- detail table

## Current Limits

- The project is local-first and not yet containerized.
- Dagster files are still scaffolding; orchestration is not implemented.
- FastAPI files are still scaffolding.
- Forecasting and MLflow are planned but not implemented.
- Regex QA still needs manual review and iterative taxonomy refinement.
