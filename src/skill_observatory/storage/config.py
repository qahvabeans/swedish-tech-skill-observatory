import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Expected a boolean value, got {value!r}")


def _required_environment(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class StorageSettings:
    endpoint: str
    access_key: str = field(repr=False)
    secret_key: str = field(repr=False)
    bucket: str
    region: str = "us-east-1"
    secure: bool = False

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> "StorageSettings":
        if env_file is not None:
            load_dotenv(dotenv_path=env_file, override=False)

        return cls(
            endpoint=_required_environment("S3_ENDPOINT"),
            access_key=_required_environment("S3_ACCESS_KEY"),
            secret_key=_required_environment("S3_SECRET_KEY"),
            bucket=_required_environment("S3_BUCKET"),
            region=os.getenv("S3_REGION", "us-east-1"),
            secure=_parse_bool(os.getenv("S3_USE_SSL", "false")),
        )
