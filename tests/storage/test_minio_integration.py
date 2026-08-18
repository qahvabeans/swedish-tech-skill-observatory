import os
from pathlib import Path

import duckdb
import pytest

from skill_observatory.storage import ObjectStorage, StorageSettings


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_MINIO_INTEGRATION_TESTS") != "1",
    reason="Set RUN_MINIO_INTEGRATION_TESTS=1 to test against local MinIO",
)
def test_minio_parquet_round_trip(tmp_path: Path) -> None:
    storage = ObjectStorage(StorageSettings.from_env())
    connection = duckdb.connect()
    object_name = "bronze/test/test.parquet"

    storage.ensure_bucket()
    storage.write_query_as_parquet(
        connection,
        "select * from (values (1, 'Data Engineer'), (2, 'Data Scientist')) "
        "as ads(id, headline)",
        object_name,
    )

    try:
        assert storage.object_exists(object_name)
        downloaded = storage.download_file(object_name, tmp_path / "test.parquet")
        rows = connection.read_parquet(str(downloaded)).fetchall()
        assert rows == [(1, "Data Engineer"), (2, "Data Scientist")]
    finally:
        storage.remove_object(object_name)
