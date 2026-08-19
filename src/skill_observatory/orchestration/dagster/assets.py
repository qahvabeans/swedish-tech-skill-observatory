from pathlib import Path

import dagster as dg
import duckdb

from skill_observatory.ingestion.pipelines.load_historical_ads import (
    run as load_historical_ads,
)
from skill_observatory.storage import ObjectStorage, StorageSettings
from skill_observatory.storage.bronze import HistoricalAdsBronzeExporter
from skill_observatory.transformations.build_historical_regex_skill_qa import (
    build_historical_regex_skill_qa,
)
from skill_observatory.transformations.build_historical_regex_skills import (
    build_historical_regex_skills,
)
from skill_observatory.transformations.run_dbt import invoke_dbt


DUCKDB_PATH = Path("data/warehouse/skill_observatory.duckdb")


class HistoricalIngestionConfig(dg.Config):
    years: list[int] = [2025]
    append: bool = True


class RegexAssetConfig(dg.Config):
    rebuild: bool = False


def _table_exists(table_name: str) -> bool:
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as connection:
        return (
            connection.sql(
                """
                select count(*)
                from information_schema.tables
                where table_schema = current_schema()
                  and table_name = ?
                """,
                params=[table_name],
            ).fetchone()[0]
            > 0
        )


@dg.asset(group_name="ingestion", compute_kind="Python + DuckDB")
def historical_ads_ingestion(
    context: dg.AssetExecutionContext,
    config: HistoricalIngestionConfig,
) -> list[int]:
    context.log.info("Loading historical archives for years: %s", config.years)
    load_historical_ads(years=config.years, append=config.append)

    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as connection:
        row = connection.sql(
            f"""
            select count(*), count(distinct id)
            from historical_job_ads
            where source_year in ({", ".join(map(str, config.years))})
            """
        ).fetchone()
    context.add_output_metadata(
        {
            "source_years": config.years,
            "rows": row[0],
            "distinct_ads": row[1],
        }
    )
    return config.years


@dg.asset(group_name="bronze", compute_kind="MinIO + Parquet")
def bronze_job_ads(
    context: dg.AssetExecutionContext,
    historical_ads_ingestion: list[int],
) -> list[int]:
    settings = StorageSettings.from_env()
    with duckdb.connect(str(DUCKDB_PATH)) as connection:
        reports = HistoricalAdsBronzeExporter(
            connection,
            ObjectStorage(settings),
        ).export(historical_ads_ingestion)

    context.add_output_metadata(
        {
            "bucket": settings.bucket,
            "partitions": len(reports),
            "rows": sum(report.source.rows for report in reports),
            "quality_passed": all(report.passed for report in reports),
        }
    )
    return historical_ads_ingestion


@dg.asset(group_name="silver", compute_kind="DuckDB regex")
def regex_skill_mentions(
    context: dg.AssetExecutionContext,
    bronze_job_ads: list[int],
    config: RegexAssetConfig,
) -> list[int]:
    should_rebuild = config.rebuild or not _table_exists("historical_regex_skills")
    if should_rebuild:
        build_historical_regex_skills()
    else:
        context.log.info(
            "Reusing historical_regex_skills; set rebuild=true after taxonomy changes."
        )
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as connection:
        row_count = connection.sql(
            "select count(*) from historical_regex_skills"
        ).fetchone()[0]
    context.add_output_metadata({"rows": row_count, "rebuilt": should_rebuild})
    return bronze_job_ads


@dg.asset(group_name="quality", compute_kind="DuckDB")
def regex_skill_quality(
    context: dg.AssetExecutionContext,
    regex_skill_mentions: list[int],
    config: RegexAssetConfig,
) -> list[int]:
    should_rebuild = config.rebuild or not _table_exists(
        "historical_regex_skill_qa_summary"
    )
    if should_rebuild:
        build_historical_regex_skill_qa()
    else:
        context.log.info(
            "Reusing regex QA tables; set rebuild=true to regenerate QA samples."
        )
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as connection:
        row_count = connection.sql(
            "select count(*) from historical_regex_skill_qa_summary"
        ).fetchone()[0]
    context.add_output_metadata(
        {"qa_summary_rows": row_count, "rebuilt": should_rebuild}
    )
    return regex_skill_mentions


@dg.asset(group_name="gold", compute_kind="dbt-duckdb")
def dbt_gold_marts(
    context: dg.AssetExecutionContext,
    regex_skill_quality: list[int],
) -> dg.MaterializeResult:
    invoke_dbt(["build"], target="minio")
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as connection:
        trend_rows = connection.sql(
            "select count(*) from mart_dashboard_skill_trends"
        ).fetchone()[0]
        geography_rows = connection.sql(
            "select count(*) from mart_skill_geography"
        ).fetchone()[0]
    return dg.MaterializeResult(
        metadata={
            "source_years": regex_skill_quality,
            "trend_rows": trend_rows,
            "geography_rows": geography_rows,
            "dbt_target": "minio",
        }
    )
