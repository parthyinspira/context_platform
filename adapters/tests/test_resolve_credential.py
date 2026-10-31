import logging

from adapters.secret_store.env import EnvSecretStore
from adapters.secret_store.resolve import CredentialNotFoundError, resolve_credential


def test_resolve_credential_success(monkeypatch) -> None:
    monkeypatch.setenv("GIT_REPO_TOKEN", "s3cr3t-value")
    store = EnvSecretStore()

    assert resolve_credential("GIT_REPO_TOKEN", store) == "s3cr3t-value"


def test_resolve_credential_missing_key_raises_without_leaking_value(monkeypatch) -> None:
    monkeypatch.delenv("DOES_NOT_EXIST_REF", raising=False)
    store = EnvSecretStore()

    try:
        resolve_credential("DOES_NOT_EXIST_REF", store)
        assert False, "expected CredentialNotFoundError"
    except CredentialNotFoundError as exc:
        assert "DOES_NOT_EXIST_REF" in str(exc)


def test_resolve_credential_never_logs_the_value(monkeypatch, caplog) -> None:
    monkeypatch.setenv("ANOTHER_SECRET_REF", "top-s3cr3t")
    store = EnvSecretStore()

    with caplog.at_level(logging.DEBUG):
        resolve_credential("ANOTHER_SECRET_REF", store)

    for record in caplog.records:
        assert "top-s3cr3t" not in record.getMessage()


def test_resolve_credential_missing_key_error_never_contains_other_env_values(monkeypatch) -> None:
    monkeypatch.setenv("UNRELATED_SECRET", "should-never-appear")
    monkeypatch.delenv("MISSING_REF", raising=False)
    store = EnvSecretStore()

    try:
        resolve_credential("MISSING_REF", store)
        assert False, "expected CredentialNotFoundError"
    except CredentialNotFoundError as exc:
        assert "should-never-appear" not in str(exc)
