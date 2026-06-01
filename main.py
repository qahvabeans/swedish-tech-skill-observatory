import subprocess
import sys

from skill_observatory.ingestion.pipelines.load_ads import run as load_ads
from skill_observatory.ingestion.pipelines.load_historical_ads import run as load_historical_ads

from skill_observatory.transformations.build_job_skill_lists import (
    build_job_skill_lists,
)

from skill_observatory.transformations.build_job_skills import (
    build_job_skills,
)

from skill_observatory.transformations.build_historical_job_skills import (
    build_historical_job_skills,
)


def main():

    print("=== Loading live ads ===")
    load_ads()

    print("=== Loading historical ads ===")
    load_historical_ads()

    print("=== Building job skill lists ===")
    build_job_skill_lists()

    print("=== Building job skills ===")
    build_job_skills()

    print("=== Building historical job skills ===")
    build_historical_job_skills()

    print("=== Starting dashboard ===")

    subprocess.run(
        [
            "streamlit",
            "run",
            "src/skill_observatory/dashboard/Home.py",
        ]
    )


if __name__ == "__main__":
    main()