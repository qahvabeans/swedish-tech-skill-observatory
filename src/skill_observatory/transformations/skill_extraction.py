import re


TECH_SKILLS = {
    "python": [
        r"\bpython\b",
    ],
    "r": [
        r"\br[-\s]?programmering\b",
        r"\br programming\b",
        r"\br language\b",
    ],
    "sql": [
        r"\bsql\b",
        r"\bt[-\s]?sql\b",
        r"\bpl/sql\b",
    ],
    "postgresql": [
        r"\bpostgres\b",
        r"\bpostgresql\b",
    ],
    "mysql": [
        r"\bmysql\b",
    ],
    "sql_server": [
        r"\bsql server\b",
        r"\bmicrosoft sql\b",
    ],
    "oracle": [
        r"\boracle\b",
    ],
    "mongodb": [
        r"\bmongodb\b",
        r"\bmongo db\b",
    ],
    "redis": [
        r"\bredis\b",
    ],
    "elasticsearch": [
        r"\belasticsearch\b",
        r"\belastic search\b",
    ],
    "aws": [
        r"\baws\b",
        r"\bamazon web services\b",
    ],
    "azure": [
        r"\bazure\b",
        r"\bmicrosoft azure\b",
    ],
    "gcp": [
        r"\bgcp\b",
        r"\bgoogle cloud\b",
        r"\bgoogle cloud platform\b",
    ],
    "azure_data_factory": [
        r"\bazure data factory\b",
        r"\badf\b",
    ],
    "azure_synapse": [
        r"\bazure synapse\b",
        r"\bsynapse analytics\b",
    ],
    "bigquery": [
        r"\bbigquery\b",
        r"\bbig query\b",
    ],
    "redshift": [
        r"\bredshift\b",
        r"\bamazon redshift\b",
    ],
    "docker": [
        r"\bdocker\b",
    ],
    "kubernetes": [
        r"\bkubernetes\b",
        r"\bk8s\b",
    ],
    "terraform": [
        r"\bterraform\b",
    ],
    "ansible": [
        r"\bansible\b",
    ],
    "jenkins": [
        r"\bjenkins\b",
    ],
    "github_actions": [
        r"\bgithub actions\b",
    ],
    "devops": [
        r"\bdevops\b",
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
        r"\bdata build tool\b",
    ],
    "snowflake": [
        r"\bsnowflake\b",
    ],
    "kafka": [
        r"\bkafka\b",
        r"\bapache kafka\b",
    ],
    "flink": [
        r"\bflink\b",
        r"\bapache flink\b",
    ],
    "hadoop": [
        r"\bhadoop\b",
    ],
    "data_engineering": [
        r"\bdata engineering\b",
        r"\bdata engineer\b",
        r"\bdataingenjor\b",
        r"\bdataingenjör\b",
    ],
    "power_bi": [
        r"\bpower\s?bi\b",
        r"\bpowerbi\b",
        r"\bpower bi desktop\b",
    ],
    "tableau": [
        r"\btableau\b",
    ],
    "qlik": [
        r"\bqlik\b",
        r"\bqlikview\b",
        r"\bqlik sense\b",
    ],
    "looker": [
        r"\blooker\b",
        r"\blooker studio\b",
    ],
    "excel": [
        r"\bexcel\b",
        r"\bmicrosoft excel\b",
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
    "javascript": [
        r"\bjavascript\b",
        r"\bjava script\b",
    ],
    "typescript": [
        r"\btypescript\b",
        r"\btype script\b",
    ],
    "java": [
        r"\bjava\b",
    ],
    "csharp": [
        r"(?<!\w)c#(?!\w)",
        r"\bcsharp\b",
        r"\bc sharp\b",
    ],
    "cpp": [
        r"(?<!\w)c\+\+(?!\w)",
    ],
    "dotnet": [
        r"(?<!\w)\.net\b",
        r"\bdotnet\b",
        r"\basp\.net\b",
    ],
    "nodejs": [
        r"\bnode\.?js\b",
        r"\bnode js\b",
    ],
    "react": [
        r"\breact\b",
        r"\breact\.js\b",
    ],
    "angular": [
        r"\bangular\b",
    ],
    "vue": [
        r"\bvue\b",
        r"\bvue\.js\b",
    ],
    "go": [
        r"\bgolang\b",
        r"\bgo programming\b",
    ],
    "rust": [
        r"\brust\b",
    ],
    "scala": [
        r"\bscala\b",
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
        r"\bpy torch\b",
    ],
    "machine_learning": [
        r"\bmachine learning\b",
        r"\bmaskininlarning\b",
        r"\bmaskininlärning\b",
    ],
    "ai": [
        r"\bai engineer\b",
        r"\bai model\b",
        r"\bai models\b",
        r"\bartificial intelligence\b",
        r"\bartificiell intelligens\b",
    ],
    "llm": [
        r"\bllm\b",
        r"\bllms\b",
        r"\blarge language model\b",
        r"\blarge language models\b",
    ],
    "openai": [
        r"\bopenai\b",
        r"\bazure openai\b",
    ],
    "langchain": [
        r"\blangchain\b",
    ],
    "rag": [
        r"\brag\b",
        r"\bretrieval augmented generation\b",
    ],
    "nlp": [
        r"\bnlp\b",
        r"\bnatural language processing\b",
        r"\bsprakbehandling\b",
        r"\bspråkbehandling\b",
    ],
}


def extract_skill_matches(text: str | None) -> list[dict[str, str]]:
    if not text:
        return []

    matches = []

    for skill, patterns in TECH_SKILLS.items():
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)

            if match:
                matches.append(
                    {
                        "skill": skill,
                        "matched_text": match.group(0),
                    }
                )
                break

    return sorted(matches, key=lambda match: match["skill"])


def extract_skills(text: str | None) -> list[str]:
    return [
        match["skill"]
        for match in extract_skill_matches(text)
    ]
