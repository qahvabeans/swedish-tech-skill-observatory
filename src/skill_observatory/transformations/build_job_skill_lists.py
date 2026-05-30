import duckdb
import pandas as pd

from skill_observatory.transformations.skill_extraction import extract_skills


def build_job_skill_lists() -> None:
    con = duckdb.connect("data/warehouse/skill_observatory.duckdb")

    ads = con.sql(
        """
        select
            id,
            headline,
            description__text
        from main.job_ads
        """
    ).df()

    ads["search_text"] = (
        ads["headline"].fillna("")
        + " "
        + ads["description__text"].fillna("")
    )

    result = ads[["id"]].copy()

    result["skills"] = (
        ads["search_text"]
        .apply(extract_skills)
    )

    con.register("job_skill_lists_df", result)

    con.sql(
        """
        create or replace table job_skill_lists as
        select *
        from job_skill_lists_df
        """
    )

    print(
        con.sql(
            """
            select *
            from job_skill_lists
            limit 10
            """
        ).df()
    )


if __name__ == "__main__":
    build_job_skill_lists()