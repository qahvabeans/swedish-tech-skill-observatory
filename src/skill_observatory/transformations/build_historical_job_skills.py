import duckdb


def build_historical_job_skills() -> None:

    con = duckdb.connect(
        "data/warehouse/skill_observatory.duckdb"
    )

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

    print(
        con.sql(
            """
            select *
            from historical_job_skills
            limit 20
            """
        )
    )

    print(
        con.sql(
            """
            select
                count(*) as rows
            from historical_job_skills
            """
        )
    )

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
        )
    )

    print(
        con.sql(
            """
            create or replace table monthly_skill_counts as

            select
            publication_month,
            skill,
            count(*) as mentions
            from historical_job_skills
            group by 1,2
            """
        )
    )

if __name__ == "__main__":
    build_historical_job_skills()