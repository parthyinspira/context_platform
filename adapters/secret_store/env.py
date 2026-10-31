import os

from .base import SecretStore


class EnvSecretStore(SecretStore):
    """Default SecretStore: process environment variables / Docker secrets."""

    def get(self, key: str) -> str | None:
        return os.environ.get(key)
