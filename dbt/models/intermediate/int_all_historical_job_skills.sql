select
    id,
    publication_month,
    skill,
    skill_source
from {{ source('warehouse', 'historical_job_skills') }}

union all

select
    id,
    publication_month,
    skill,
    skill_source
from {{ source('warehouse', 'historical_regex_skills') }}
