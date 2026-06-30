{{ config(enabled=var('include_regex_qa', false)) }}

select
    skill,
    count(distinct id) as ads,
    count(*) as matches,
    count(distinct lower(matched_text)) as matched_terms
from {{ source('warehouse', 'historical_regex_skill_matches') }}
group by 1
