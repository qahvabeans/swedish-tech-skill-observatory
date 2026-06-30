select
    publication_month,
    skill,
    count(distinct id) as mentions
from {{ source('warehouse', 'historical_regex_skills') }}
group by 1, 2
