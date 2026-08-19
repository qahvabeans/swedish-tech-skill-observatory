# Archived Fabric Proof Of Concept

This folder preserves a completed Microsoft Fabric trial experiment that mapped
the local DuckDB/dbt project to a Lakehouse-oriented data engineering project.

The trial and its Azure resources are no longer active. Nothing in the default
pipeline depends on Fabric. The files remain useful as a portfolio artifact and
as a reproducible template for a future Fabric environment.

## Target Fabric Layout

```text
Fabric workspace
  |
  +-- Lakehouse: skill_observatory_lakehouse
  |     |
  |     +-- Files/bronze/historical_job_ads/*.parquet
  |     +-- Files/silver/historical_regex_skills/*.parquet
  |     +-- Files/silver/historical_regex_skill_qa_summary/*.parquet
  |     +-- Files/gold/monthly_skill_counts/*.parquet
  |     +-- Files/gold/mart_dashboard_skill_trends/*.parquet
  |     +-- Files/gold/mart_skill_geography/*.parquet
  |
  +-- Notebook: 01_load_bronze_to_lakehouse
  +-- Notebook: 02_build_silver_skill_tables
  +-- Notebook: 03_build_gold_skill_marts
  +-- Notebook: 04_forecasting_mvp
  |
  +-- Report: Swedish Tech Skill Observatory
```

## Local Export

Run the normal local pipeline first:

```powershell
python -m skill_observatory.transformations.build_historical_regex_skills
python -m skill_observatory.transformations.build_historical_regex_skill_qa
dbt build --profiles-dir .
```

Then export Fabric-ready Parquet files:

```powershell
python -m skill_observatory.fabric.export_fabric_tables
```

By default the export is written to `data/fabric_export/`.

To export only gold marts for a smaller Fabric demo:

```powershell
python -m skill_observatory.fabric.export_fabric_tables --layers gold
```

The export casts monthly date columns to `DATE` because the Fabric SQL analytics
endpoint does not support every Parquet timestamp variant emitted by local
engines.

## Recreating The Experiment

1. Provision an eligible Microsoft Fabric capacity.
2. Create a workspace, for example `swedish-skill-observatory-dev`.
3. Create a Lakehouse named `skill_observatory_lakehouse`.
4. Upload the exported Parquet folders from `data/fabric_export/`.
5. Create Lakehouse tables from the uploaded Parquet files.
6. Create one notebook per pipeline layer, even if the first version only reads
   and writes the exported tables.
7. Create a simple report with skill trends, Top N skills, growth, and geography.
8. Add screenshots to `fabric/screenshots/`.

## Fabric Pipeline

The repository includes a Fabric Data Pipeline definition under
`fabric/workspace/skill_observatory_historical_pipeline.DataPipeline/`.

Import it with Fabric CLI:

```powershell
fab import /swedish-skill-observatory-dev.Workspace/skill_observatory_historical_pipeline.DataPipeline -i fabric/workspace/skill_observatory_historical_pipeline.DataPipeline -f
```

Before importing from the repository, replace the placeholder IDs in
`pipeline-content.json` with the workspace and notebook item IDs from your own
Fabric workspace. The live proof-of-concept pipeline can also be created in the
Fabric UI and kept as the runtime copy, while the repository stores the
shareable template.

The current pipeline mirrors the local project at a proof-of-concept level:

- `01_bronze_ingest_historical_ads` reads uploaded Bronze Parquet files and
  writes a Delta table.
- `02_silver_extract_regex_skills` applies a compact regex taxonomy and writes
  one row per ad and skill.
- `03_gold_build_skill_marts` builds monthly, normalized, and geographic Gold
  marts for reports.

The Fabric notebooks are intentionally smaller than the local DuckDB/dbt
implementation. They show the architecture and transformation pattern while the
local project remains the richer source of truth for historical ingestion and
regex QA.

## Screenshot Checklist

Capture these screenshots for the portfolio documentation:

- Fabric workspace overview with Lakehouse, notebooks, and report.
- Lakehouse files or tables showing bronze, silver, and gold folders.
- Notebook that reads a bronze table and writes or validates a silver table.
- SQL endpoint or Lakehouse table preview for `mart_dashboard_skill_trends`.
- Report page showing technology skill trend analysis.
- Optional: capacity metrics view if it helps discuss operations and monitoring.
