import pytest

from skill_observatory.storage.config import StorageSettings


def test_storage_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        "S3_ENDPOINT": "localhost:9000",
        "S3_ACCESS_KEY": "test-access",
        "S3_SECRET_KEY": "test-secret",
        "S3_BUCKET": "test-bucket",
        "S3_REGION": "eu-north-1",
        "S3_USE_SSL": "true",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    settings = StorageSettings.from_env(env_file=None)

    assert settings.endpoint == "localhost:9000"
    assert settings.bucket == "test-bucket"
    assert settings.region == "eu-north-1"
    assert settings.secure is True
    assert "test-secret" not in repr(settings)


def test_storage_settings_reject_invalid_boolean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("S3_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("S3_ACCESS_KEY", "test-access")
    monkeypatch.setenv("S3_SECRET_KEY", "test-secret")
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    monkeypatch.setenv("S3_USE_SSL", "sometimes")

    with pytest.raises(ValueError, match="Expected a boolean value"):
        StorageSettings.from_env(env_file=None)
