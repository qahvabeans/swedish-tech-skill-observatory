from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

import duckdb
from minio import Minio

from skill_observatory.storage.config import StorageSettings


class MinioClient(Protocol):
    def bucket_exists(self, bucket_name: str) -> bool: ...

    def make_bucket(self, bucket_name: str, location: str | None = None) -> None: ...

    def stat_object(self, bucket_name: str, object_name: str): ...

    def fput_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        content_type: str | None = None,
    ): ...

    def fget_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
    ): ...

    def remove_object(self, bucket_name: str, object_name: str) -> None: ...


class ObjectStorage:
    def __init__(
        self,
        settings: StorageSettings,
        client: MinioClient | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or Minio(
            endpoint=settings.endpoint,
            access_key=settings.access_key,
            secret_key=settings.secret_key,
            secure=settings.secure,
            region=settings.region,
        )

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.settings.bucket):
            self.client.make_bucket(
                self.settings.bucket,
                location=self.settings.region,
            )

    def object_exists(self, object_name: str) -> bool:
        try:
            self.client.stat_object(self.settings.bucket, object_name)
        except Exception as exc:
            if getattr(exc, "code", None) in {"NoSuchKey", "NoSuchObject"}:
                return False
            raise
        return True

    def upload_file(self, source: str | Path, object_name: str) -> None:
        self.client.fput_object(
            self.settings.bucket,
            object_name,
            str(source),
            content_type="application/vnd.apache.parquet",
        )

    def download_file(self, object_name: str, destination: str | Path) -> Path:
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        self.client.fget_object(
            self.settings.bucket,
            object_name,
            str(destination_path),
        )
        return destination_path

    def remove_object(self, object_name: str) -> None:
        self.client.remove_object(self.settings.bucket, object_name)

    def write_query_as_parquet(
        self,
        connection: duckdb.DuckDBPyConnection,
        query: str,
        object_name: str,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            parquet_path = Path(temp_dir) / "data.parquet"
            connection.sql(query).write_parquet(str(parquet_path))
            self.upload_file(parquet_path, object_name)
