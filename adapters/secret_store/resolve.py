"""Resolve a `sources.credentials_ref` key into an actual secret value.

This is the single function any harvester (or other component) uses to turn a
stored reference key into a secret. It never logs the resolved value, and any
error it raises carries only the reference key, never a secret value.
"""
from .base import SecretStore


class CredentialNotFoundError(Exception):
    """Raised when a `credentials_ref` key does not resolve in the SecretStore.

    The message carries only the `credentials_ref` key, never a secret value.
    """

    def __init__(self, credentials_ref: str) -> None:
        super().__init__(f"credentials_ref {credentials_ref!r} did not resolve in SecretStore")
        self.credentials_ref = credentials_ref


def resolve_credential(credentials_ref: str, secret_store: SecretStore) -> str:
    """Resolve `credentials_ref` to its secret value via `secret_store`.

    Raises `CredentialNotFoundError` (key only, no value) if the store has no
    value for this key.
    """
    value = secret_store.get(credentials_ref)
    if value is None:
        raise CredentialNotFoundError(credentials_ref)
    return value
