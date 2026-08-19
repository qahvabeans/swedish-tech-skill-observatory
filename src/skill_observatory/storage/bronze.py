import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

from skill_observatory.storage.client import ObjectStorage


@dataclass(frozen=True)
class PartitionMetrics:
    rows: int
    distinct_ads: int
    first_publication_date: str | None
    last_publication_date: str | None
    null_ids: int
    null_publication_months: int


@dataclass(frozen=True)
class BronzeQualityReport:
    source_year: int
    object_name: str
    parquet_bytes: int
    source: PartitionMetrics
    object_storage: PartitionMetrics
    passed: bool


def _serialize_temporal(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _metrics(
    connection: duckdb.DuckDBPyConnection,
    relation_sql: str,
) -> PartitionMetrics:
    row = connection.sql(
        f"""
        select
            count(*) as rows,
            count(distinct id) as distinct_ads,
            min(publication_date) as first_publication_date,
            max(publication_date) as last_publication_date,
            count(*) filter (where id is null) as null_ids,
            count(*) filter (where publication_month is null)
                as null_publication_months
        from ({relation_sql})
        """
    ).fetchone()
    return PartitionMetrics(
        rows=row[0],
        distinct_ads=row[1],
        first_publication_date=_serialize_temporal(row[2]),
        last_publication_date=_serialize_temporal(row[3]),
        null_ids=row[4],
        null_publication_months=row[5],
    )


class HistoricalAdsBronzeExporter:
    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        storage: ObjectStorage,
    ) -> None:
        self.connection = connection
        self.storage = storage

    def available_years(self) -> list[int]:
        return [
            row[0]
            for row in self.connection.sql(
                """
                select distinct source_year
                from historical_job_ads
                where source_year is not null
                order by source_year
                """
            ).fetchall()
        ]

    def export(self, years: list[int] | None = None) -> list[BronzeQualityReport]:
        selected_years = years or self.available_years()
        if not selected_years:
            raise ValueError("No source years are available for Bronze export")

        self.storage.ensure_bucket()
        reports = []
        for index, source_year in enumerate(selected_years, start=1):
            print(
                f"Step {index}/{len(selected_years)}: exporting source_year={source_year}"
            )
            reports.append(self.export_year(source_year))
        return reports

    def export_year(self, source_year: int) -> BronzeQualityReport:
        source_query = (
            "select * exclude(source_year) from historical_job_ads "
            f"where source_year = {int(source_year)}"
        )
        source_metrics = _metrics(self.connection, source_query)
        if source_metrics.rows == 0:
            raise ValueError(f"No historical ads found for source_year={source_year}")

        partition_prefix = f"bronze/job_ads/source_year={source_year}/"
        object_name = f"{partition_prefix}part-000.parquet"
        quality_name = f"quality/bronze/job_ads/source_year={source_year}.json"

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            parquet_path = temp_path / "part-000.parquet"
            downloaded_path = temp_path / "downloaded.parquet"
            report_path = temp_path / "quality.json"

            self.connection.sql(source_query).write_parquet(
                str(parquet_path),
                compression="zstd",
            )
            self.storage.upload_file(
                parquet_path,
                object_name,
                content_type="application/vnd.apache.parquet",
            )
            self.storage.remove_prefix(partition_prefix, keep={object_name})
            self.storage.download_file(object_name, downloaded_path)

            parquet_sql = (
                "select * from read_parquet(" f"'{downloaded_path.as_posix()}'" ")"
            )
            object_metrics = _metrics(self.connection, parquet_sql)
            report = BronzeQualityReport(
                source_year=source_year,
                object_name=object_name,
                parquet_bytes=parquet_path.stat().st_size,
                source=source_metrics,
                object_storage=object_metrics,
                passed=source_metrics == object_metrics,
            )
            report_path.write_text(
                json.dumps(asdict(report), indent=2, ensure_ascii=True),
                encoding="utf-8",
            )
            self.storage.upload_file(
                report_path,
                quality_name,
                content_type="application/json",
            )

        if not report.passed:
            raise RuntimeError(
                f"Bronze quality validation failed for source_year={source_year}"
            )
        print(
            f"source_year={source_year}, rows={report.source.rows:,}, "
            f"distinct_ads={report.source.distinct_ads:,}, "
            f"parquet_mb={report.parquet_bytes / 1024 / 1024:.1f}, quality=passed"
        )
        return report
