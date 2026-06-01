import re


TECH_SKILLS = {
    "python": [
        r"\bpython\b",
    ],
    "sql": [
        r"\bsql\b",
    ],
    "aws": [
        r"\baws\b",
        r"\bamazon web services\b",
    ],
    "azure": [
        r"\bazure\b",
    ],
    "gcp": [
        r"\bgcp\b",
        r"\bgoogle cloud\b",
    ],
    "docker": [
        r"\bdocker\b",
    ],
    "kubernetes": [
        r"\bkubernetes\b",
        r"\bk8s\b",
    ],
    "spark": [
        r"\bspark\b",
        r"\bapache spark\b",
        r"\bpyspark\b",
    ],
    "databricks": [
        r"\bdatabricks\b",
    ],
    "airflow": [
        r"\bairflow\b",
        r"\bapache airflow\b",
    ],
    "dbt": [
        r"\bdbt\b",
    ],
    "snowflake": [
        r"\bsnowflake\b",
    ],
    "power_bi": [
        r"\bpower\s?bi\b",
    ],
    "tableau": [
        r"\btableau\b",
    ],
    "git": [
        r"\bgit\b",
    ],
    "github": [
        r"\bgithub\b",
    ],
    "gitlab": [
        r"\bgitlab\b",
    ],
    "pandas": [
        r"\bpandas\b",
    ],
    "numpy": [
        r"\bnumpy\b",
    ],
    "scikit_learn": [
        r"\bscikit[\-\s]?learn\b",
        r"\bsklearn\b",
    ],
    "tensorflow": [
        r"\btensorflow\b",
    ],
    "pytorch": [
        r"\bpytorch\b",
    ],
    "llm": [
        r"\bllm\b",
        r"\blarge language model\b",
    ],
    "openai": [
        r"\bopenai\b",
    ],
    "langchain": [
        r"\blangchain\b",
    ],
}


def extract_skills(text: str | None) -> list[str]:
    if not text:
        return []

    text = text.lower()

    matches = set()

    for skill, patterns in TECH_SKILLS.items():

        for pattern in patterns:

            if re.search(pattern, text):
                matches.add(skill)
                break

    return sorted(matches)