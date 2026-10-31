from adapters.secret_store.env import EnvSecretStore


def test_get_returns_env_value(monkeypatch) -> None:
    monkeypatch.setenv("SOME_SECRET", "s3cr3t")
    store = EnvSecretStore()

    assert store.get("SOME_SECRET") == "s3cr3t"


def test_get_missing_key_returns_none(monkeypatch) -> None:
    monkeypatch.delenv("DOES_NOT_EXIST", raising=False)
    store = EnvSecretStore()

    assert store.get("DOES_NOT_EXIST") is None
