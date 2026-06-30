import duckdb
from pathlib import Path

def build_ams_skill_catalogue() -> None:
    con = duckdb.connect("data/warehouse/skill_observatory.duckdb")

    con.sql(
        """
        create or replace table ams_skill_catalogue as

        select
            skill,
            count(distinct id) as ads,
            count(*) as mentions
        from historical_job_skills
        group by 1
        order by ads desc
        """
    )

    print(
        con.sql(
            """
            select *
            from ams_skill_catalogue
            order by ads desc
            limit 100
            """
        ).df()
    )

    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    con.sql("""
        copy ams_skill_catalogue
        to 'data/exports/ams_skill_catalogue.csv'
        (header, delimiter ',')
    """)

    print("Exported to data/exports/ams_skill_catalogue.csv")

if __name__ == "__main__":
    build_ams_skill_catalogue()