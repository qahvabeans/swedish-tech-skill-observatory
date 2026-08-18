# Roadmap

## Completed / Implemented

- Local historical ingestion from yearly Platsbanken-related JSONL archives.
- Batch loading with `--years` and idempotent archive replacement with
  `--append`.
- DuckDB warehouse table for historical job ads.
- DuckDB-native regex skill extraction.
- Regex QA summary and sample tables.
- AMS skill extraction retained as a secondary comparison source.
- dbt project with staging, intermediate, and dashboard mart models.
- dbt tests for source validity, share bounds, and mart consistency.
- Streamlit dashboard with trends, Top N, growth, tables, and geography view.
- Geography mart by month, skill, municipality, and region.
- Archived Fabric proof-of-concept notebooks, pipeline definition, and local
  Parquet export helper.

## Next Priorities

### 1. Add Local Object Storage

- Run MinIO through Docker Compose with credentials from local environment
  variables.
- Create the `skill-observatory` bucket automatically.
- Add central S3-compatible storage configuration.
- Add a small tested storage client for Parquet objects.

### 2. Migrate Bronze Data Incrementally

- Keep the working DuckDB ingestion while also writing historical ads as
  partitioned Parquet under `bronze/job_ads/`.
- Configure DuckDB to query Parquet directly from MinIO.
- Preserve downstream dbt contracts while changing their upstream relation.
- Compare row counts and business metrics with the existing DuckDB pipeline.

### 3. Add Orchestration

- Convert ingestion, extraction, and dbt build steps into Dagster assets.
- Add dependencies, lineage, materialization metadata, and data quality checks.
- Add partitions and backfill support for historical archive periods.

### 4. Forecasting MVP

- Use `monthly_skill_counts` or `mart_dashboard_skill_trends` as input.
- Start with simple classical baselines.
- Evaluate short-term forecasts for selected technology skills.
- Track experiments with MLflow after the first baseline works.

### 5. Improve Dashboard Polish

- Make the dashboard visually cleaner and more portfolio-ready.
- Add clearer labels, formatting, and explanatory text.
- Improve map presentation and metric formatting.
- Add screenshots to the README.

### 6. Expand And Review Regex Taxonomy

- Review `historical_regex_skill_samples`.
- Remove false positives.
- Add missing aliases for Swedish and English tech terms.
- Split overly broad skills where useful.

### 7. Improve Reproducibility

- Expand Docker Compose after the MinIO foundation is stable.
- Add a small sample dataset for public/demo runs.
- Add CI checks for ruff and dbt parse/build where sample data allows.

## Future Improvements

- Add FastAPI backend for serving dashboard/API consumers.
- Add richer geographic views and regional comparisons.
- Add occupation/industry segmentation.
- Consider NLP or LLM-assisted extraction after the regex baseline is measured.
- Publish a cleaned portfolio demo with screenshots and architecture diagram.
- Consider Delta Lake only when schema evolution, upserts, or time travel solve
  a demonstrated need.
