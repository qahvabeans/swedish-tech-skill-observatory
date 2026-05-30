from collections.abc import Iterable


SKILLS = [
    "python",
    "sql",
    "aws",
    "dbt",
    "docker",
    "kubernetes",
    "spark",
    "databricks",
    "airflow",
    "dagster",
    "pandas",
    "git",
    "fiskar", # just to check if it works
]


def extract_skills(text: str | None) -> list[str]:
    """
    Return unique skills found in text.
    """

    if not text:
        return []

    text = text.lower()

    matches = {
        skill
        for skill in SKILLS
        if skill in text
    }

    return sorted(matches)