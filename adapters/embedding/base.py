from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Text-embedding interface. No provider SDK types in the signature."""

    @abstractmethod
    def embed(self, texts: list[str]) -> tuple[list[list[float]], str]:
        """Return (one vector per input text, embedding_model name)."""
