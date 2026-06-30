import duckdb

from skill_observatory.transformations.skill_extraction import extract_skill_matches


DUCKDB_PATH = "data/warehouse/skill_observatory.duckdb"
SAMPLES_PER_SKILL = 20


def build_historical_regex_skill_qa() -> None:
    """Build regex extraction QA tables for manual skill review.

    Input table:
        historical_job_ads

    Output tables:
        historical_regex_skill_matches
        historical_regex_skill_qa_summary
        historical_regex_skill_samples
    """

    con = duckdb.connect(DUCKDB_PATH)

    ads = con.sql(
        """
        select
            id,
            publication_month,
            headline,
            description_text,
            coalesce(headline, '') || ' ' || coalesce(description_text, '') as search_text
        from historical_job_ads
        """
    ).df()

    ads["matches"] = ads["search_text"].apply(extract_skill_matches)

    matches = (
        ads[
            [
                "id",
                "publication_month",
                "headline",
                "description_text",
                "matches",
            ]
        ]
        .explode("matches")
        .dropna(subset=["matches"])
    )

    if matches.empty:
        con.sql(
            """
            create or replace table historical_regex_skill_matches (
                id varchar,
                publication_month timestamp,
                skill varchar,
                matched_text varchar,
                headline varchar,
                description_snippet varchar
            )
            """
        )
    else:
        matches["skill"] = matches["matches"].apply(lambda match: match["skill"])
        matches["matched_text"] = matches["matches"].apply(
            lambda match: match["matched_text"]
        )
        matches["description_snippet"] = (
            matches["description_text"]
            .fillna("")
            .str.replace(r"\s+", " ", regex=True)
            .str.slice(0, 400)
        )

        con.register("historical_regex_skill_matches_df", matches)

        con.sql(
            """
            create or replace table historical_regex_skill_matches as
            select
                id,
                publication_month,
                skill,
                matched_text,
                headline,
                description_snippet
            from historical_regex_skill_matches_df
            """
        )

    con.sql(
        """
        create or replace table historical_regex_skill_qa_summary as
        select
            skill,
            count(distinct id) as ads,
            count(*) as matches,
            count(distinct lower(matched_text)) as matched_terms
        from historical_regex_skill_matches
        group by 1
        order by ads desc
        """
    )

    con.sql(
        f"""
        create or replace table historical_regex_skill_samples as

        with ranked as (

            select
                *,
                row_number() over (
                    partition by skill
                    order by publication_month desc, id
                ) as sample_rank
            from historical_regex_skill_matches

        )

        select
            skill,
            matched_text,
            id,
            publication_month,
            headline,
            description_snippet
        from ranked
        where sample_rank <= {SAMPLES_PER_SKILL}
        order by skill, sample_rank
        """
    )

    print("\n=== regex skill QA summary ===")
    print(
        con.sql(
            """
            select *
            from historical_regex_skill_qa_summary
            limit 30
            """
        ).df()
    )


if __name__ == "__main__":
    build_historical_regex_skill_qa()
