import argparse
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import duckdb


DUCKDB_PATH = "data/warehouse/skill_observatory.duckdb"
RAW_DIR = Path("data/raw")
TEMP_DIR = Path("data/temp")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load JobTech historical JSONL zip archives into DuckDB.",
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        help="Only load these archive years, for example: --years 2024 2025.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help=(
            "Keep the existing historical_job_ads table and replace only the "
            "selected archive rows. Without this flag, the table is rebuilt."
        ),
    )

    return parser.parse_args()


def _sql_string(value: str) -> str:
    return value.replace("'", "''")


def _extract_archive(zip_path: Path, destination_dir: Path) -> Path:
    with ZipFile(zip_path) as z:
        jsonl_files = [
            name
            for name in z.namelist()
            if name.endswith(".jsonl")
        ]

        if len(jsonl_files) != 1:
            raise ValueError(
                f"Expected exactly one JSONL file in {zip_path}, found {len(jsonl_files)}"
            )

        jsonl_file = jsonl_files[0]
        extracted_path = destination_dir / Path(jsonl_file).name

        with z.open(jsonl_file) as source:
            with extracted_path.open("wb") as target:
                copyfileobj(source, target)

    return extracted_path


def _historical_ads_select(
    extracted_path: Path,
    source_archive: str,
    source_year: int,
) -> str:
    json_path = _sql_string(extracted_path.as_posix())
    archive = _sql_string(source_archive)
    occupation_label = "occupation.label" if source_year == 2022 else "occupation[1].label"
    occupation_group_label = (
        "occupation_group.label"
        if source_year == 2022
        else "occupation_group[1].label"
    )
    occupation_field_label = (
        "occupation_field.label"
        if source_year == 2022
        else "occupation_field[1].label"
    )

    return f"""
select
    id,

    publication_date,

    date_trunc(
        'month',
        publication_date
    ) as publication_month,

    headline,

    description.text as description_text,

    {occupation_label} as occupation,

    {occupation_group_label} as occupation_group,

    {occupation_field_label} as occupation_field,

    must_have.skills as must_have_skills,

    nice_to_have.skills as nice_to_have_skills,

    workplace_address.municipality::varchar as municipality,

    workplace_address.municipality_code::varchar as municipality_code,

    workplace_address.region::varchar as region,

    workplace_address.region_code::varchar as region_code,

    workplace_address.postcode::varchar as postcode,

    workplace_address.city::varchar as city,

    workplace_address.coordinates[1]::double as longitude,

    workplace_address.coordinates[2]::double as latitude,

    '{archive}' as source_archive,

    {source_year} as source_year

from read_json_auto(
    '{json_path}',
    records=true,
    ignore_errors=true
)
"""


def _table_exists(con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    return (
        con.sql(
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


def _archive_year(zip_path: Path) -> int:
    return int(zip_path.stem.split(".")[0])


def _archive_paths(years: list[int] | None) -> list[Path]:
    archive_paths = sorted(RAW_DIR.glob("*.jsonl.zip"))

    if years:
        requested_years = set(years)
        archive_paths = [
            path
            for path in archive_paths
            if _archive_year(path) in requested_years
        ]
        found_years = {
            _archive_year(path)
            for path in archive_paths
        }
        missing_years = sorted(requested_years - found_years)

        if missing_years:
            raise FileNotFoundError(
                f"No historical archives found for years: {missing_years}"
            )

    if not archive_paths:
        raise FileNotFoundError(f"No historical archives found in {RAW_DIR}")

    return archive_paths


def _print_archive_validation(
    con: duckdb.DuckDBPyConnection,
    source_archive: str,
) -> None:
    row = con.sql(
        """
        select
            source_archive,
            count(*) as rows,
            min(publication_date) as first_publication_date,
            max(publication_date) as last_publication_date,
            count(distinct id) as distinct_ads
        from historical_job_ads
        where source_archive = ?
        group by 1
        """,
        params=[source_archive],
    ).fetchone()

    print(
        "source_archive={source_archive}, rows={rows}, distinct_ads={distinct_ads}, "
        "first_publication_date={first_date}, last_publication_date={last_date}".format(
            source_archive=row[0],
            rows=row[1],
            first_date=row[2],
            last_date=row[3],
            distinct_ads=row[4],
        )
    )


def run(
    years: list[int] | None = None,
    append: bool = False,
) -> None:
    archive_paths = _archive_paths(years)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(DUCKDB_PATH)
    table_exists = _table_exists(con, "historical_job_ads")

    with TemporaryDirectory(dir=TEMP_DIR) as temp_dir:
        extraction_dir = Path(temp_dir)

        for index, zip_path in enumerate(archive_paths):
            source_year = _archive_year(zip_path)
            source_archive = zip_path.name
            extracted_path = _extract_archive(zip_path, extraction_dir)
            select_sql = _historical_ads_select(
                extracted_path=extracted_path,
                source_archive=source_archive,
                source_year=source_year,
            )

            print(f"\n=== Loading {source_archive} ===")

            should_create_table = (
                index == 0
                and (
                    not append
                    or not table_exists
                )
            )

            if should_create_table:
                con.sql(
                    f"""
                    create or replace table historical_job_ads as
                    {select_sql}
                    """
                )
                table_exists = True
            else:
                if append:
                    con.sql(
                        """
                        delete from historical_job_ads
                        where source_archive = ?
                        """,
                        params=[source_archive],
                    )

                con.sql(
                    f"""
                    insert into historical_job_ads
                    {select_sql}
                    """
                )

            _print_archive_validation(con, source_archive)

    print("\n=== historical_job_ads total ===")
    row = con.sql(
        """
        select
            count(*) as rows,
            count(distinct id) as distinct_ads,
            min(publication_date) as first_publication_date,
            max(publication_date) as last_publication_date
        from historical_job_ads
        """
    ).fetchone()

    print(
        "rows={rows}, distinct_ads={distinct_ads}, first_publication_date={first_date}, "
        "last_publication_date={last_date}".format(
            rows=row[0],
            distinct_ads=row[1],
            first_date=row[2],
            last_date=row[3],
        )
    )


if __name__ == "__main__":
    args = _parse_args()
    run(
        years=args.years,
        append=args.append,
    )
