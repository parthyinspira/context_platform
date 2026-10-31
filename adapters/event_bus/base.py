from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Event:
    id: str
    topic: str
    payload: dict[str, Any]


class EventBus(ABC):
    """Publish/poll interface for domain events. Cloud-neutral: no SDK types in the signature."""

    @abstractmethod
    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Durably record an event on a topic."""

    @abstractmethod
    def poll(self, topic: str, limit: int = 10) -> list[Event]:
        """Return up to `limit` undelivered events for `topic` and mark them delivered."""
