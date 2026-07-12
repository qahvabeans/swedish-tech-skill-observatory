with skill_ads as (

    select
        id,
        publication_month,
        skill
    from {{ source('warehouse', 'historical_regex_skills') }}

),

ad_locations as (

    select
        id,
        publication_month,
        municipality,
        municipality_code,
        coalesce(region, 'Unknown') as region,
        coalesce(region_code, 'unknown') as region_code,
        longitude,
        latitude
    from {{ ref('stg_historical_job_ads') }}
    where municipality is not null
      and longitude between 10 and 25
      and latitude between 55 and 70

),

monthly_location_ads as (

    select
        publication_month,
        municipality_code,
        count(distinct id) as ads
    from ad_locations
    group by 1, 2

)

select
    skill_ads.publication_month,
    skill_ads.skill,
    ad_locations.municipality,
    ad_locations.municipality_code,
    ad_locations.region,
    ad_locations.region_code,
    avg(ad_locations.longitude) as longitude,
    avg(ad_locations.latitude) as latitude,
    count(distinct skill_ads.id) as mentions,
    max(monthly_location_ads.ads) as ads,
    count(distinct skill_ads.id)::double
        / nullif(max(monthly_location_ads.ads), 0) as share_of_ads
from skill_ads
inner join ad_locations
    on skill_ads.id = ad_locations.id
    and skill_ads.publication_month = ad_locations.publication_month
left join monthly_location_ads
    on ad_locations.publication_month = monthly_location_ads.publication_month
    and ad_locations.municipality_code = monthly_location_ads.municipality_code
group by
    skill_ads.publication_month,
    skill_ads.skill,
    ad_locations.municipality,
    ad_locations.municipality_code,
    ad_locations.region,
    ad_locations.region_code
