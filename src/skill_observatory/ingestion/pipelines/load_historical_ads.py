from zipfile import ZipFile
import duckdb


def run() -> None:

    zip_path = "data/raw/2025.jsonl.zip"

    with ZipFile(zip_path) as z:
        jsonl_file = z.namelist()[0]

        z.extract(
            jsonl_file,
            path="data/temp",
        )

    extracted_path = f"data/temp/{jsonl_file}"

    con = duckdb.connect("data/warehouse/skill_observatory.duckdb")

    con.sql(f"""
create or replace table historical_job_ads as

select
    id,

    publication_date,

    date_trunc(
        'month',
        publication_date
    ) as publication_month,

    headline,

    description.text as description_text,

    occupation[1].label as occupation,

    occupation_group[1].label as occupation_group,

    occupation_field[1].label as occupation_field,

    must_have.skills as must_have_skills,

    nice_to_have.skills as nice_to_have_skills

from read_json_auto(
    '{extracted_path}',
    records=true,
    ignore_errors=true
)
""")
    

if __name__ == "__main__":
    run()
