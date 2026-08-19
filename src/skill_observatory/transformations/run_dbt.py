import argparse

from dbt.cli.main import dbtRunner
from dotenv import load_dotenv


def invoke_dbt(command: list[str], target: str = "minio") -> None:
    load_dotenv(override=False)
    arguments = [*command, "--profiles-dir", ".", "--target", target]
    result = dbtRunner().invoke(arguments)
    if not result.success:
        raise RuntimeError(
            f"dbt command failed for target={target}: {' '.join(command)}"
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run dbt after loading local environment settings."
    )
    parser.add_argument("--target", default="minio", choices=["dev", "minio"])
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="dbt command and arguments; defaults to build",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    invoke_dbt(args.command or ["build"], target=args.target)
