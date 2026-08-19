import dagster as dg

from skill_observatory.orchestration.dagster.assets import (
    bronze_job_ads,
    dbt_gold_marts,
    historical_ads_ingestion,
    regex_skill_mentions,
    regex_skill_quality,
)
from skill_observatory.orchestration.dagster.jobs import historical_pipeline_job
from skill_observatory.orchestration.dagster.schedules import (
    monthly_historical_pipeline_schedule,
)


defs = dg.Definitions(
    assets=[
        historical_ads_ingestion,
        bronze_job_ads,
        regex_skill_mentions,
        regex_skill_quality,
        dbt_gold_marts,
    ],
    jobs=[historical_pipeline_job],
    schedules=[monthly_historical_pipeline_schedule],
)
