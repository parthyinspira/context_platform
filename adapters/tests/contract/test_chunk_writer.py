from adapters.chunks.writer import PostgresChunkWriter
from adapters.embedding.base import EmbeddingProvider

from .fake_chunks_postgres import FakeChunksConnection


class StubEmbeddingProvider(EmbeddingProvider):
    def __init__(self, vectors: list[list[float]], model: str):
        self._vectors = vectors
        self._model = model
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> tuple[list[list[float]], str]:
        self.calls.append(texts)
        return self._vectors, self._model


def test_write_records_embedding_model_from_provider() -> None:
    conn = FakeChunksConnection()
    provider = StubEmbeddingProvider(vectors=[[0.1, 0.2, 0.3]], model="nomic-embed-text")
    writer = PostgresChunkWriter(lambda: conn, provider)

    chunk_id = writer.write("entity-1", "source-1", "hello world", metadata={"section": "intro"})

    assert len(conn.rows) == 1
    row = conn.rows[0]
    assert row.id == chunk_id
    assert row.entity_id == "entity-1"
    assert row.source_id == "source-1"
    assert row.text == "hello world"
    assert row.embedding == [0.1, 0.2, 0.3]
    assert row.embedding_model == "nomic-embed-text"
    assert row.embedding_model  # never empty/None
    assert row.metadata == {"section": "intro", "sensitivity": "internal"}
    assert conn.committed == 1


def test_write_never_lets_caller_set_embedding_model() -> None:
    # ChunkWriter.write has no embedding_model parameter at all: the model name
    # can only come from the EmbeddingProvider's own return value.
    import inspect

    from adapters.chunks.base import ChunkWriter

    params = inspect.signature(ChunkWriter.write).parameters
    assert "embedding_model" not in params


def test_write_defaults_metadata_to_empty_dict() -> None:
    conn = FakeChunksConnection()
    provider = StubEmbeddingProvider(vectors=[[1.0]], model="nomic-embed-text")
    writer = PostgresChunkWriter(lambda: conn, provider)

    writer.write("entity-1", "source-1", "no metadata given")

    assert conn.rows[0].metadata == {"sensitivity": "internal"}


def test_write_redacts_secrets_before_storage_and_sets_sensitivity() -> None:
    conn = FakeChunksConnection()
    provider = StubEmbeddingProvider(vectors=[[0.1]], model="nomic-embed-text")
    writer = PostgresChunkWriter(lambda: conn, provider)
    fake_secret = "AKIAFAKEEXAMPLE12345"  # seeded fixture, not a real AWS key

    writer.write("entity-1", "source-1", f"config has {fake_secret} inline")

    row = conn.rows[0]
    assert fake_secret not in row.text
    assert "[REDACTED:aws_access_key_id]" in row.text
    assert row.metadata["sensitivity"] == "restricted"
    assert row.metadata["redacted"] is True
    # The raw secret must never reach the embedding provider either.
    assert all(fake_secret not in call_text for call in provider.calls for call_text in call)
