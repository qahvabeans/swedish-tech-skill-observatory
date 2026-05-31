from collections.abc import Iterable
import re


SKILLS = [
    "python",
    "sql",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "spark",
    "databricks",
    "dbt",
    "airflow",
    "dagster",
    "git",
    "pandas",
    "power bi",
    "tableau",
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
        if re.search(rf"\b{re.escape(skill)}\b", text)
    }

    return sorted(matches)