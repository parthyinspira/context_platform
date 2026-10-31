import json
import uuid
from typing import Any, Protocol

from adapters.embedding.base import EmbeddingProvider
from adapters.scanning import scan_and_redact

from .base import ChunkWriter


class DBConnection(Protocol):
    """Minimal DB-API-shaped connection (psycopg or any compatible driver)."""

    def cursor(self) -> Any: ...
    def commit(self) -> None: ...


class PostgresChunkWriter(ChunkWriter):
    """Default ChunkWriter: embeds via the configured `EmbeddingProvider`, then
    inserts one row into the `chunks` table (migrations/0001_core_tables.up.sql).

    Takes a connection factory, matching `PostgresOutboxEventBus`, so each call
    gets a fresh connection/cursor.
    """

    def __init__(self, connection_factory: Any, embedding_provider: EmbeddingProvider):
        self._connection_factory = connection_factory
        self._embedding_provider = embedding_provider

    def write(
        self,
        entity_id: str,
        source_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        # Scan for secrets/PII and redact before anything is embedded or stored.
        # See spec/capabilities/harvester-framework.md "Read-only and secret-safe"
        # and docs/HARVESTERS.md rule 8 (Secrets and PII).
        scan_result = scan_and_redact(text)
        stored_text = scan_result.redacted_text

        stored_metadata = dict(metadata or {})
        stored_metadata["sensitivity"] = scan_result.sensitivity
        if scan_result.findings:
            stored_metadata["redacted"] = True

        vectors, embedding_model = self._embedding_provider.embed([stored_text])
        chunk_id = str(uuid.uuid4())

        conn = self._connection_factory()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chunks "
            "(id, entity_id, source_id, text, embedding, embedding_model, metadata) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                chunk_id,
                entity_id,
                source_id,
                stored_text,
                vectors[0],
                embedding_model,
                json.dumps(stored_metadata),
            ),
        )
        conn.commit()
        return chunk_id
