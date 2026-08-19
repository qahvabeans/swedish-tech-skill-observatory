import duckdb

from skill_observatory.storage.config import StorageSettings


def _sql_string(value: str) -> str:
    return value.replace("'", "''")


def configure_minio(
    connection: duckdb.DuckDBPyConnection,
    settings: StorageSettings,
) -> None:
    connection.execute("INSTALL httpfs")
    connection.execute("LOAD httpfs")
    connection.execute(
        f"""
        create or replace secret minio_object_storage (
            type s3,
            provider config,
            key_id '{_sql_string(settings.access_key)}',
            secret '{_sql_string(settings.secret_key)}',
            region '{_sql_string(settings.region)}',
            endpoint '{_sql_string(settings.endpoint)}',
            url_style 'path',
            use_ssl {str(settings.secure).lower()},
            scope 's3://{_sql_string(settings.bucket)}'
        )
        """
    )


def historical_ads_parquet_glob(settings: StorageSettings) -> str:
    return f"s3://{settings.bucket}/bronze/job_ads/**/*.parquet"


def create_historical_ads_external_view(
    connection: duckdb.DuckDBPyConnection,
    settings: StorageSettings,
    view_name: str = "historical_job_ads_external",
) -> None:
    configure_minio(connection, settings)
    connection.execute(
        f"""
        create or replace view {view_name} as
        select *
        from read_parquet(
            '{_sql_string(historical_ads_parquet_glob(settings))}',
            hive_partitioning = true,
            union_by_name = true
        )
        """
    )


def count_historical_ads(
    connection: duckdb.DuckDBPyConnection,
    settings: StorageSettings,
) -> int:
    configure_minio(connection, settings)
    return (
        connection.read_parquet(
            historical_ads_parquet_glob(settings),
            hive_partitioning=True,
            union_by_name=True,
        )
        .aggregate("count(*)")
        .fetchone()[0]
    )
