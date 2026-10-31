from abc import ABC, abstractmethod


class ObjectStore(ABC):
    """Raw-object storage interface. Cloud-neutral: keys are strings, values are bytes."""

    @abstractmethod
    def put(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def get(self, key: str) -> bytes: ...

    @abstractmethod
    def list(self, prefix: str = "") -> list[str]: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...
