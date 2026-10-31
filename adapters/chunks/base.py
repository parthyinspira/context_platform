from abc import ABC, abstractmethod
from typing import Any


class ChunkWriter(ABC):
    """Writes a chunk of text (plus its embedding) for an entity.

    Implementations MUST obtain `embedding_model` from the `EmbeddingProvider`
    they embed with, never from the caller, so every `chunks` row records
    which model produced its vector.
    """

    @abstractmethod
    def write(
        self,
        entity_id: str,
        source_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Embed `text`, insert a `chunks` row, and return the new chunk id."""
