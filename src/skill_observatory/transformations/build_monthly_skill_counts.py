import duckdb


DUCKDB_PATH = "data/warehouse/skill_observatory.duckdb"


def build_monthly_skill_counts() -> None:
    """Build historical skill source tables and regex-primary monthly aggregates.

    Required input tables:
        historical_job_skills      -- AMS-provided skills
        historical_regex_skills    -- project-specific regex skills

    Output tables:
        all_historical_job_skills
        monthly_skill_counts

    monthly_skill_counts is intentionally based on historical_regex_skills only.
    AMS skills are retained in all_historical_job_skills for comparison and QA,
    but the dashboard-facing trend table uses the project regex taxonomy as the
    primary source.
    """

    con = duckdb.connect(DUCKDB_PATH)

    con.sql(
        """
        create or replace table all_historical_job_skills as

        select
            id,
            publication_month,
            skill,
            skill_source
        from historical_job_skills

        union all

        select
            id,
            publication_month,
            skill,
            skill_source
        from historical_regex_skills
        """
    )

    con.sql(
        """
        create or replace table monthly_skill_counts as

        select
            publication_month,
            skill,
            count(distinct id) as mentions
        from historical_regex_skills
        group by 1, 2
        """
    )

    print("\n=== skill sources ===")
    print(
        con.sql(
            """
            select
                skill_source,
                count(*) as rows
            from all_historical_job_skills
            group by 1
            order by 2 desc
            """
        ).df()
    )

    print("\n=== monthly_skill_counts sample ===")
    print(
        con.sql(
            """
            select *
            from monthly_skill_counts
            order by publication_month desc, mentions desc
            limit 20
            """
        ).df()
    )

    print("\n=== top regex skills overall ===")
    print(
        con.sql(
            """
            select
                skill,
                sum(mentions) as mentions
            from monthly_skill_counts
            group by 1
            order by 2 desc
            limit 30
            """
        ).df()
    )


if __name__ == "__main__":
    build_monthly_skill_counts()
