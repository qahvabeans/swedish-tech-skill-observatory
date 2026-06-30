with monthly_ads as (

    select
        publication_month,
        count(distinct id) as ads
    from {{ ref('stg_historical_job_ads') }}
    group by 1

),

monthly_skills as (

    select
        publication_month,
        skill,
        mentions
    from {{ ref('monthly_skill_counts') }}

)

select
    monthly_skills.publication_month,
    monthly_skills.skill,
    monthly_skills.mentions,
    monthly_ads.ads,
    monthly_skills.mentions::double / nullif(monthly_ads.ads, 0) as share_of_ads
from monthly_skills
inner join monthly_ads
    on monthly_skills.publication_month = monthly_ads.publication_month
