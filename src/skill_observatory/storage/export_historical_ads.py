import argparse
from pathlib import Path

import duckdb

from skill_observatory.storage import ObjectStorage, StorageSettings
from skill_observatory.storage.bronze import HistoricalAdsBronzeExporter


DEFAULT_DUCKDB_PATH = Path("data/warehouse/skill_observatory.duckdb")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export historical DuckDB ads to partitioned Bronze Parquet in MinIO."
    )
    parser.add_argument("--years", type=int, nargs="+")
    parser.add_argument("--duckdb-path", type=Path, default=DEFAULT_DUCKDB_PATH)
    return parser.parse_args()


def run(
    years: list[int] | None = None,
    duckdb_path: Path = DEFAULT_DUCKDB_PATH,
) -> None:
    settings = StorageSettings.from_env()
    storage = ObjectStorage(settings)
    with duckdb.connect(str(duckdb_path)) as connection:
        reports = HistoricalAdsBronzeExporter(connection, storage).export(years)

    total_rows = sum(report.source.rows for report in reports)
    print(
        f"Bronze export complete: partitions={len(reports)}, rows={total_rows:,}, "
        f"bucket={settings.bucket}"
    )


if __name__ == "__main__":
    args = _parse_args()
    run(years=args.years, duckdb_path=args.duckdb_path)
