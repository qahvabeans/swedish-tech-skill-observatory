import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


def invoke_dbt(command: list[str], target: str = "minio") -> None:
    load_dotenv(override=False)
    executable_name = "dbt.exe" if os.name == "nt" else "dbt"
    dbt_executable = Path(sys.executable).with_name(executable_name)
    if not dbt_executable.exists():
        raise FileNotFoundError(
            f"dbt executable was not found next to Python: {dbt_executable}"
        )

    arguments = [
        str(dbt_executable),
        *command,
        "--profiles-dir",
        ".",
        "--target",
        target,
    ]
    subprocess.run(arguments, check=True)


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
