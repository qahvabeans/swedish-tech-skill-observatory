from pathlib import Path
from shutil import copyfile

import duckdb

from skill_observatory.storage import ObjectStorage, StorageSettings


class FakeMinioClient:
    def __init__(self, object_dir: Path) -> None:
        self.object_dir = object_dir
        self.bucket_created = False

    def bucket_exists(self, bucket_name: str) -> bool:
        return self.bucket_created

    def make_bucket(self, bucket_name: str, location: str | None = None) -> None:
        self.bucket_created = True

    def stat_object(self, bucket_name: str, object_name: str) -> object:
        if not (self.object_dir / object_name).exists():
            error = RuntimeError("Object does not exist")
            error.code = "NoSuchKey"  # type: ignore[attr-defined]
            raise error
        return object()

    def fput_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        content_type: str | None = None,
    ) -> None:
        destination = self.object_dir / object_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        copyfile(file_path, destination)

    def fget_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
    ) -> None:
        copyfile(self.object_dir / object_name, file_path)

    def remove_object(self, bucket_name: str, object_name: str) -> None:
        (self.object_dir / object_name).unlink()

    def list_objects(
        self,
        bucket_name: str,
        prefix: str | None = None,
        recursive: bool = False,
    ) -> list[object]:
        selected_prefix = prefix or ""
        objects = []
        if self.object_dir.exists():
            for path in self.object_dir.rglob("*"):
                if path.is_file():
                    object_name = path.relative_to(self.object_dir).as_posix()
                    if object_name.startswith(selected_prefix):
                        objects.append(type("Object", (), {"object_name": object_name})())
        return objects


def test_write_and_read_parquet_object(tmp_path: Path) -> None:
    settings = StorageSettings(
        endpoint="localhost:9000",
        access_key="test-access",
        secret_key="test-secret",
        bucket="test-bucket",
    )
    fake_client = FakeMinioClient(tmp_path / "objects")
    storage = ObjectStorage(settings, client=fake_client)
    connection = duckdb.connect()
    object_name = "bronze/test/test.parquet"

    storage.ensure_bucket()
    storage.write_query_as_parquet(
        connection,
        "select * from (values (1, 'Data Engineer'), (2, 'Data Scientist')) "
        "as ads(id, headline)",
        object_name,
    )

    assert storage.object_exists(object_name)

    downloaded = storage.download_file(object_name, tmp_path / "download.parquet")
    rows = connection.read_parquet(str(downloaded)).fetchall()

    assert rows == [(1, "Data Engineer"), (2, "Data Scientist")]
