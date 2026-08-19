from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


DUCKDB_PATH = Path("data/warehouse/skill_observatory.duckdb")
DEFAULT_OUTPUT_DIR = Path("data/fabric_export")


EXPORT_TABLES = {
    "bronze": [
        ("historical_job_ads", "bronze/historical_job_ads"),
    ],
    "silver": [
        ("historical_regex_skills", "silver/historical_regex_skills"),
        ("historical_regex_skill_qa_summary", "silver/historical_regex_skill_qa_summary"),
    ],
    "gold": [
        ("monthly_skill_counts", "gold/monthly_skill_counts"),
        ("mart_dashboard_skill_trends", "gold/mart_dashboard_skill_trends"),
        ("mart_skill_geography", "gold/mart_skill_geography"),
    ],
}


FABRIC_SELECTS = {
    "monthly_skill_counts": """
        select
            cast(publication_month as date) as publication_month,
            skill,
            mentions
        from monthly_skill_counts
    """,
    "mart_dashboard_skill_trends": """
        select
            cast(publication_month as date) as publication_month,
            skill,
            mentions,
            ads,
            share_of_ads
        from mart_dashboard_skill_trends
    """,
    "mart_skill_geography": """
        select
            cast(publication_month as date) as publication_month,
            skill,
            municipality,
            municipality_code,
            region,
            region_code,
            longitude,
            latitude,
            mentions,
            ads,
            share_of_ads
        from mart_skill_geography
    """,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export DuckDB tables as Parquet files for a Fabric Lakehouse demo."
    )
    parser.add_argument(
        "--duckdb-path",
        type=Path,
        default=DUCKDB_PATH,
        help="Path to the local DuckDB warehouse.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where Fabric-ready Parquet files should be written.",
    )
    parser.add_argument(
        "--layers",
        nargs="+",
        choices=["bronze", "silver", "gold", "all"],
        default=["all"],
        help="Medallion layers to export.",
    )
    return parser.parse_args()


def selected_layers(layers: list[str]) -> list[str]:
    if "all" in layers:
        return list(EXPORT_TABLES)
    return layers


def export_table(con: duckdb.DuckDBPyConnection, table_name: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = con.sql(f"select count(*) as row_count from {table_name}").fetchone()[0]
    export_select = FABRIC_SELECTS.get(table_name, f"select * from {table_name}")
    print(f"Exporting {table_name} ({row_count:,} rows) -> {output_path}")
    con.sql(
        f"""
        copy ({export_select})
        to '{output_path.as_posix()}'
        (format parquet, compression zstd);
        """
    )


def run(duckdb_path: Path, output_dir: Path, layers: list[str]) -> None:
    if not duckdb_path.exists():
        raise FileNotFoundError(
            f"DuckDB warehouse not found at {duckdb_path}. Run the local pipeline first."
        )

    print(f"Connecting to {duckdb_path}")
    con = duckdb.connect(str(duckdb_path), read_only=True)

    for layer in selected_layers(layers):
        print(f"\n=== Exporting {layer} layer ===")
        for table_name, relative_output in EXPORT_TABLES[layer]:
            export_table(
                con=con,
                table_name=table_name,
                output_path=output_dir / relative_output / "part-000.parquet",
            )

    con.close()
    print(f"\nFabric export complete: {output_dir}")


if __name__ == "__main__":
    args = parse_args()
    run(
        duckdb_path=args.duckdb_path,
        output_dir=args.output_dir,
        layers=args.layers,
    )
