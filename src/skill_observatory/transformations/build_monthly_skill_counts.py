import duckdb


def build_monthly_skill_counts() -> None:
    con = duckdb.connect("data/warehouse/skill_observatory.duckdb")

    con.sql(
        """
        create or replace table monthly_skill_counts as

        select
            date_trunc('month', publication_date) as month,
            skill,
            count(*) as mentions

        from job_skills

        group by
            1,
            2

        order by
            month,
            mentions desc
        """
    )

    print(
        con.sql(
            """
            select *
            from monthly_skill_counts
            limit 20
            """
        ).df()
    )


if __name__ == "__main__":
    build_monthly_skill_counts()