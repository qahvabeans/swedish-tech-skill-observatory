select 1
where not exists (
    select 1
    from {{ ref('monthly_skill_counts') }}
)
