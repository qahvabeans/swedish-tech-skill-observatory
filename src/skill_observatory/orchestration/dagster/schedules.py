import dagster as dg

from skill_observatory.orchestration.dagster.jobs import historical_pipeline_job


monthly_historical_pipeline_schedule = dg.ScheduleDefinition(
    job=historical_pipeline_job,
    cron_schedule="0 6 2 * *",
    default_status=dg.DefaultScheduleStatus.STOPPED,
    description="Monthly refresh; intentionally stopped by default for local use.",
)
