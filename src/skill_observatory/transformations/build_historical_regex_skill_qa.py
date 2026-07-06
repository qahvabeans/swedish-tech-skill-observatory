from time import perf_counter

import duckdb


DUCKDB_PATH = "data/warehouse/skill_observatory.duckdb"
SAMPLES_PER_SKILL = 20


def _table_exists(con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    return (
        con.sql(
            """
            select count(*)
            from information_schema.tables
            where table_schema = current_schema()
              and table_name = ?
            """,
            params=[table_name],
        ).fetchone()[0]
        > 0
    )


def _print_elapsed(step: str, started_at: float) -> None:
    elapsed = perf_counter() - started_at
    print(f"{step} finished in {elapsed:,.1f}s")


def build_historical_regex_skill_qa() -> None:
    """Build regex extraction QA tables for manual skill review.

    Input table:
        historical_regex_skill_matches

    Output tables:
        historical_regex_skill_qa_summary
        historical_regex_skill_samples
    """

    started_at = perf_counter()
    con = duckdb.connect(DUCKDB_PATH)

    if not _table_exists(con, "historical_regex_skill_matches"):
        raise RuntimeError(
            "historical_regex_skill_matches does not exist. "
            "Run build_historical_regex_skills first."
        )

    match_count = con.sql(
        """
        select count(*)
        from historical_regex_skill_matches
        """
    ).fetchone()[0]

    print(
        "=== Building regex skill QA ===\n"
        f"Using {match_count:,} rows from historical_regex_skill_matches"
    )

    step_started_at = perf_counter()
    print("Step 1/3: creating historical_regex_skill_qa_summary")
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
    _print_elapsed("Step 1/3", step_started_at)

    step_started_at = perf_counter()
    print("Step 2/3: creating historical_regex_skill_samples")
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
    _print_elapsed("Step 2/3", step_started_at)

    step_started_at = perf_counter()
    print("Step 3/3: printing regex skill QA summary")
    print(
        con.sql(
            """
            select *
            from historical_regex_skill_qa_summary
            limit 30
            """
        ).df()
    )
    _print_elapsed("Step 3/3", step_started_at)
    _print_elapsed("regex skill QA build", started_at)


if __name__ == "__main__":
    build_historical_regex_skill_qa()
