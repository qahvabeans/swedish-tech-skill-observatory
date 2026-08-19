from dataclasses import dataclass

import duckdb

from skill_observatory.storage import StorageSettings
from skill_observatory.storage.duckdb_s3 import (
    configure_minio,
    historical_ads_parquet_glob,
)
from skill_observatory.transformations.run_dbt import invoke_dbt


DUCKDB_PATH = "data/warehouse/skill_observatory.duckdb"
PARITY_TABLES = (
    "monthly_skill_counts",
    "mart_dashboard_skill_trends",
    "mart_skill_geography",
)
STAGING_HASH_COLUMNS = (
    "id",
    "publication_date",
    "publication_month",
    "headline",
    "description_text",
    "occupation",
    "occupation_group",
    "occupation_field",
    "municipality",
    "municipality_code",
    "region",
    "region_code",
    "postcode",
    "city",
    "longitude",
    "latitude",
    "source_archive",
    "source_year",
)


@dataclass(frozen=True)
class StagingMetrics:
    rows: int
    distinct_ads: int
    first_publication_date: str
    last_publication_date: str
    null_ids: int
    null_publication_months: int
    content_hash: int


@dataclass(frozen=True)
class ParityResult:
    table_name: str
    local_rows: int
    minio_rows: int
    differing_rows: int

    @property
    def passed(self) -> bool:
        return self.local_rows == self.minio_rows and self.differing_rows == 0


def _staging_metrics(
    connection: duckdb.DuckDBPyConnection,
    relation_sql: str,
) -> StagingMetrics:
    hash_arguments = ", ".join(STAGING_HASH_COLUMNS)
    row = connection.sql(
        f"""
        select
            count(*),
            count(distinct id),
            min(publication_date)::varchar,
            max(publication_date)::varchar,
            count(*) filter (where id is null),
            count(*) filter (where publication_month is null),
            bit_xor(hash({hash_arguments}))
        from ({relation_sql})
        """
    ).fetchone()
    return StagingMetrics(*row)


def _compare_staging_sources() -> tuple[StagingMetrics, StagingMetrics]:
    settings = StorageSettings.from_env()
    with duckdb.connect(DUCKDB_PATH) as connection:
        configure_minio(connection, settings)
        local = _staging_metrics(connection, "select * from historical_job_ads")
        minio = _staging_metrics(
            connection,
            "select * from read_parquet("
            f"'{historical_ads_parquet_glob(settings)}', "
            "hive_partitioning = true, union_by_name = true)",
        )
    return local, minio


def _snapshot_local_marts() -> None:
    with duckdb.connect(DUCKDB_PATH) as connection:
        for table_name in PARITY_TABLES:
            connection.execute(
                f"""
                create or replace table parity_local_{table_name} as
                select * from {table_name}
                """
            )


def _compare_marts() -> list[ParityResult]:
    results = []
    with duckdb.connect(DUCKDB_PATH) as connection:
        try:
            for table_name in PARITY_TABLES:
                local_name = f"parity_local_{table_name}"
                local_rows = connection.sql(
                    f"select count(*) from {local_name}"
                ).fetchone()[0]
                minio_rows = connection.sql(
                    f"select count(*) from {table_name}"
                ).fetchone()[0]
                differing_rows = connection.sql(
                    f"""
                    select count(*)
                    from (
                        (select * from {local_name}
                         except all select * from {table_name})
                        union all
                        (select * from {table_name}
                         except all select * from {local_name})
                    ) differences
                    """
                ).fetchone()[0]
                results.append(
                    ParityResult(
                        table_name=table_name,
                        local_rows=local_rows,
                        minio_rows=minio_rows,
                        differing_rows=differing_rows,
                    )
                )
        finally:
            for table_name in PARITY_TABLES:
                connection.execute(f"drop table if exists parity_local_{table_name}")
    return results


def run() -> None:
    print("Step 1/5: comparing local and MinIO staging metrics and content hashes")
    local_staging, minio_staging = _compare_staging_sources()
    print(f"local_staging={local_staging}")
    print(f"minio_staging={minio_staging}")
    if local_staging != minio_staging:
        raise RuntimeError("MinIO staging parity failed")

    print("Step 2/5: building dbt marts from the local DuckDB source")
    invoke_dbt(["build"], target="dev")

    print("Step 3/5: snapshotting local analytical marts")
    _snapshot_local_marts()

    print("Step 4/5: building dbt marts directly from MinIO Bronze Parquet")
    invoke_dbt(["build"], target="minio")

    print("Step 5/5: comparing local and MinIO-backed marts")
    results = _compare_marts()
    for result in results:
        print(
            f"table={result.table_name}, local_rows={result.local_rows:,}, "
            f"minio_rows={result.minio_rows:,}, "
            f"differing_rows={result.differing_rows:,}, "
            f"status={'passed' if result.passed else 'failed'}"
        )

    failed = [result for result in results if not result.passed]
    if failed:
        raise RuntimeError(f"MinIO parity failed for {len(failed)} mart(s)")
    print("MinIO parity passed for staging and all analytical marts")


if __name__ == "__main__":
    run()
