# Roadmap

## Phase 1: Expand Historical Data

Status: in progress

- Load all historical archives from `data/raw/*.jsonl.zip`.
- Generalize historical ingestion so new yearly archives are picked up
  automatically.
- Verify row counts, date ranges, and distinct ad counts after each archive is
  loaded.
- Rebuild historical AMS skills, regex skills, and monthly aggregates after
  ingestion.

## Phase 2: Improve Skill Extraction

Status: planned

- Expand the regex-based skill taxonomy.
- Add aliases and normalization, for example `Power BI` and `powerbi` to
  `power_bi`.
- Improve Swedish and English term coverage.
- Add quality assurance for false positives and missing skills.
- Add review queries for regex source overlap and sample matched job ads.

## Phase 2.5: Data Quality and Contracts

Status: planned

- Validate required warehouse tables.
- Validate required columns and basic types.
- Check for null `id`, null `publication_month`, and impossible date ranges.
- Track row counts by source archive and skill source.
- Produce simple validation reports for each pipeline run.

## Phase 3: Enhance the Dashboard

Status: planned

- Add Top N skills by month.
- Add fastest growing and declining skills.
- Compare multiple skills in the same chart.
- Add occupation, date, and skill source filters.
- Display normalized metrics, such as share of ads, alongside raw mention
  counts.

## Phase 4: Pipeline Orchestration

Status: planned

- Replace manual execution with Dagster assets.
- Define ingestion, transformation, and aggregation as asset materializations.
- Add schedules, lineage, and run metadata.
- Improve logging and pipeline observability.

## Phase 5: Forecasting MVP

Status: planned

- Build a first forecasting pipeline from historical monthly skill counts.
- Evaluate classical time-series models such as Prophet, ARIMA, and
  Holt-Winters.
- Generate short-term forecasts for selected technology skills.
- Compare forecast accuracy across models.

## Phase 6: ML Operations

Status: planned

- Introduce MLflow for experiment tracking.
- Track model parameters and evaluation metrics.
- Version trained forecasting models.
- Prepare reproducible ML experiments.

## Future Improvements

- Introduce a FastAPI backend between DuckDB and the dashboard.
- Dockerize the full stack.
- Add automated tests for ingestion and transformations.
- Build data quality checks and validation reports.
- Consider NLP or LLM-assisted skill extraction once the regex baseline is
  stable and measurable.
