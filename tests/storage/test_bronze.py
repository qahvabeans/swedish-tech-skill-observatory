from pathlib import Path

import duckdb

from skill_observatory.storage import ObjectStorage, StorageSettings
from skill_observatory.storage.bronze import HistoricalAdsBronzeExporter
from tests.storage.test_client import FakeMinioClient


def test_export_historical_ads_partition_with_quality_report(tmp_path: Path) -> None:
    connection = duckdb.connect()
    connection.execute(
        """
        create table historical_job_ads as
        select *
        from (
            values
                ('1', timestamp '2022-01-10', date '2022-01-01', 'Engineer', 2022),
                ('2', timestamp '2022-02-11', date '2022-02-01', 'Scientist', 2022)
        ) ads(id, publication_date, publication_month, headline, source_year)
        """
    )
    settings = StorageSettings(
        endpoint="localhost:9000",
        access_key="test-access",
        secret_key="test-secret",
        bucket="test-bucket",
    )
    storage = ObjectStorage(settings, client=FakeMinioClient(tmp_path / "objects"))

    report = HistoricalAdsBronzeExporter(connection, storage).export([2022])[0]

    assert report.passed
    assert report.source.rows == 2
    assert storage.object_exists("bronze/job_ads/source_year=2022/part-000.parquet")
    assert storage.object_exists("quality/bronze/job_ads/source_year=2022.json")
