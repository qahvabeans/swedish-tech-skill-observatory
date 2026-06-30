select
    id,
    publication_date,
    publication_month,
    headline,
    description_text,
    occupation,
    occupation_group,
    occupation_field
from {{ source('warehouse', 'historical_job_ads') }}
