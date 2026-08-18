"""S3-compatible object storage helpers."""

from skill_observatory.storage.client import ObjectStorage
from skill_observatory.storage.config import StorageSettings

__all__ = ["ObjectStorage", "StorageSettings"]
