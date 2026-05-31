# build_job_skills.py

import duckdb


def build_job_skills() -> None:
    con = duckdb.connect("data/warehouse/skill_observatory.duckdb")

    df = con.sql(
        """
        select *
        from job_skill_lists
        """
    ).df()

    df = (
        df
        .explode("skills")
        .rename(columns={"skills": "skill"})
        .dropna(subset=["skill"])
    )

    con.register("job_skills_df", df)

    con.sql(
        """
        create or replace table job_skills as
        select *
        from job_skills_df
        """
    )

    print(
        con.sql(
            """
            select *
            from job_skills
            limit 10
            """
        ).df()
    )


if __name__ == "__main__":
    build_job_skills()