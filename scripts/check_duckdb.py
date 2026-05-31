import duckdb

con = duckdb.connect("data/warehouse/skill_observatory.duckdb")

con.sql("""
create or replace table skill_mentions as
select
    id,
    headline,
    case
        when lower(headline) like '%fiskarfruns%'
        then 1
        else 0
    end as mentions_python
from main.job_ads
""")


print(con.sql("""
    select *
    from skill_mentions
    limit 10
""").df())