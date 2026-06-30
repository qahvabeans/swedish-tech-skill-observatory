import duckdb

from skill_observatory.transformations.skill_extraction import extract_skills


DUCKDB_PATH = "data/warehouse/skill_observatory.duckdb"


def build_historical_regex_skills() -> None:
    """Build regex-based tech skill mentions from historical job ads.

    Input table:
        historical_job_ads

    Output table:
        historical_regex_skills

    This complements AMS skills with project-specific tech terms such as
    dbt, Snowflake, Databricks, LLM, etc.
    """

    con = duckdb.connect(DUCKDB_PATH)

    ads = con.sql(
        """
        select
            id,
            publication_month,
            coalesce(headline, '') || ' ' || coalesce(description_text, '') as search_text
        from historical_job_ads
        """
    ).df()

    ads["skills"] = ads["search_text"].apply(extract_skills)

    skills = (
        ads[["id", "publication_month", "skills"]]
        .explode("skills")
        .rename(columns={"skills": "skill"})
        .dropna(subset=["skill"])
    )

    skills["skill_source"] = "regex"

    con.register("historical_regex_skills_df", skills)

    con.sql(
        """
        create or replace table historical_regex_skills as
        select
            id,
            publication_month,
            skill,
            skill_source
        from historical_regex_skills_df
        """
    )

    print("\n=== top regex skills ===")
    print(
        con.sql(
            """
            select
                skill,
                count(*) as mentions
            from historical_regex_skills
            group by 1
            order by 2 desc
            limit 30
            """
        ).df()
    )


if __name__ == "__main__":
    build_historical_regex_skills()
