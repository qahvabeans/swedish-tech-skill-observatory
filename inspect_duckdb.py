# inspect_duckdb.py

import duckdb

con = duckdb.connect("skill_observatory.duckdb")

print(
    con.sql("""
        select *
        from information_schema.tables
    """).df()
)

print(
    con.sql(
        """
        select *
        from raw.job_ads
        limit 5
        """
    ).df()
)

print(
    con.sql("""
        select count(*)
        from raw.job_ads
    """).df()
)

print(
    con.sql("""
        select
            headline,
            publication_date
        from raw.job_ads
        limit 5
    """).df()
)