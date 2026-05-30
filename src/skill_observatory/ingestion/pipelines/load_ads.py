import dlt
from src.skill_observatory.ingestion.sources.arbetsformedlingen import fetch_ads

@dlt.resource(
    name="job_ads",
    write_disposition="replace",
)

def job_ads():
    yield fetch_ads(limit=10)

def run():
    pipeline = dlt.pipeline(
    pipeline_name="skill_observatory",
    destination="duckdb",
    dataset_name="main",
)

    info = pipeline.run(
        job_ads(),
        table_name="job_ads",
    )

    print(info)

if __name__ == "__main__":
    run()