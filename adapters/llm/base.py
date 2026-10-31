from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Chat-completion interface. No provider SDK types in the signature."""

    @abstractmethod
    def complete(self, messages: list[dict[str, str]], **options: Any) -> str:
        """Return the completion text for a list of {"role", "content"} messages."""
