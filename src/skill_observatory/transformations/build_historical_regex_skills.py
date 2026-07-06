from time import perf_counter

import duckdb

from skill_observatory.transformations.skill_extraction import TECH_SKILLS


DUCKDB_PATH = "data/warehouse/skill_observatory.duckdb"


SQL_PATTERN_OVERRIDES = {
    r"(?<!\w)c#(?!\w)": r"(^|[^[:alnum:]_])c#([^[:alnum:]_]|$)",
    r"(?<!\w)c\+\+(?!\w)": r"(^|[^[:alnum:]_])c\+\+([^[:alnum:]_]|$)",
    r"(?<!\w)\.net\b": r"(^|[^[:alnum:]_])\.net\b",
}


def _sql_string(value: str) -> str:
    return value.replace("'", "''")


def _sql_pattern(pattern: str) -> str:
    return SQL_PATTERN_OVERRIDES.get(pattern, pattern)


def _skill_patterns_values_sql() -> str:
    rows = []

    for skill, patterns in TECH_SKILLS.items():
        for pattern_order, pattern in enumerate(patterns):
            rows.append(
                "('{skill}', {pattern_order}, '{pattern}')".format(
                    skill=_sql_string(skill),
                    pattern_order=pattern_order,
                    pattern=_sql_string(_sql_pattern(pattern)),
                )
            )

    return ",\n            ".join(rows)


def _print_elapsed(step: str, started_at: float) -> None:
    elapsed = perf_counter() - started_at
    print(f"{step} finished in {elapsed:,.1f}s")


def build_historical_regex_skills() -> None:
    """Build regex-based tech skill mentions from historical job ads.

    Input table:
        historical_job_ads

    Output tables:
        historical_regex_skill_matches
        historical_regex_skills

    The regex matching runs inside DuckDB to avoid loading all ad text into
    pandas memory.
    """

    started_at = perf_counter()
    con = duckdb.connect(DUCKDB_PATH)

    ad_count = con.sql(
        """
        select count(*)
        from historical_job_ads
        """
    ).fetchone()[0]

    pattern_count = sum(
        len(patterns)
        for patterns in TECH_SKILLS.values()
    )

    print(
        "=== Building historical regex skills ===\n"
        f"Scanning {ad_count:,} ads with {pattern_count:,} regex patterns in DuckDB"
    )

    step_started_at = perf_counter()
    print("Step 1/3: creating historical_regex_skill_matches")
    con.sql(
        f"""
        create or replace table historical_regex_skill_matches as

        with patterns(skill, pattern_order, pattern) as (
            values
            {_skill_patterns_values_sql()}
        ),

        ads as (

            select
                id,
                publication_month,
                headline,
                description_text,
                coalesce(headline, '') || ' ' || coalesce(description_text, '') as search_text
            from historical_job_ads

        ),

        matches as (

            select
                ads.id,
                ads.publication_month,
                patterns.skill,
                trim(regexp_extract(ads.search_text, patterns.pattern, 0, 'i')) as matched_text,
                ads.headline,
                left(
                    regexp_replace(coalesce(ads.description_text, ''), '\\s+', ' ', 'g'),
                    400
                ) as description_snippet,
                row_number() over (
                    partition by ads.id, patterns.skill
                    order by patterns.pattern_order
                ) as match_rank
            from ads
            inner join patterns
                on regexp_matches(ads.search_text, patterns.pattern, 'i')

        )

        select
            id,
            publication_month,
            skill,
            matched_text,
            headline,
            description_snippet
        from matches
        where match_rank = 1
        """
    )
    _print_elapsed("Step 1/3", step_started_at)

    step_started_at = perf_counter()
    print("Step 2/3: creating historical_regex_skills")
    con.sql(
        """
        create or replace table historical_regex_skills as

        select
            id,
            publication_month,
            skill,
            'regex' as skill_source
        from historical_regex_skill_matches
        """
    )
    _print_elapsed("Step 2/3", step_started_at)

    step_started_at = perf_counter()
    print("Step 3/3: printing top regex skills")
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
    _print_elapsed("Step 3/3", step_started_at)
    _print_elapsed("historical regex skill build", started_at)


if __name__ == "__main__":
    build_historical_regex_skills()
