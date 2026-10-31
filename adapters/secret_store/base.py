from abc import ABC, abstractmethod


class SecretStore(ABC):
    """Secret lookup by key. Never log the returned value."""

    @abstractmethod
    def get(self, key: str) -> str | None: ...
