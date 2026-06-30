import duckdb


DUCKDB_PATH = "data/warehouse/skill_observatory.duckdb"


def build_historical_job_skills() -> None:
    """Build AMS-provided skill mentions from historical job ads.

    Input table:
        historical_job_ads

    Output table:
        historical_job_skills

    The output contains one row per job ad and AMS skill.
    """

    con = duckdb.connect(DUCKDB_PATH)

    con.sql(
        """
        create or replace table historical_job_skills as

        with skills as (

            select
                id,
                publication_month,
                unnest(must_have_skills) as skill
            from historical_job_ads

            union all

            select
                id,
                publication_month,
                unnest(nice_to_have_skills) as skill
            from historical_job_ads

        )

        select
            id,
            publication_month,
            skill.label as skill,
            'ams' as skill_source
        from skills
        where skill.label is not null
        """
    )

    print("\n=== historical_job_skills sample ===")
    print(
        con.sql(
            """
            select *
            from historical_job_skills
            limit 20
            """
        ).df()
    )

    print("\n=== historical_job_skills row count ===")
    print(
        con.sql(
            """
            select count(*) as rows
            from historical_job_skills
            """
        ).df()
    )

    print("\n=== top AMS skills ===")
    print(
        con.sql(
            """
            select
                skill,
                count(*) as mentions
            from historical_job_skills
            group by 1
            order by 2 desc
            limit 20
            """
        ).df()
    )


if __name__ == "__main__":
    build_historical_job_skills()
