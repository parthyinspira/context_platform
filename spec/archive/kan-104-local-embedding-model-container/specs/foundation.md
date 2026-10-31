# Delta for foundation

## ADDED Requirements

### Requirement: Embeddings container serves a local model
The `embeddings` container SHALL pull and serve one concrete local embedding model (`EMBEDDING_MODEL`, default `nomic-embed-text`) on startup, so `HTTPEmbeddingProvider` can call a real local model rather than an empty Ollama instance.

#### Scenario: embeddings-container-serves-local-model
- **Given** the `embeddings` container image and its entrypoint script
- **When** the container starts with `EMBEDDING_MODEL=nomic-embed-text`
- **Then** the entrypoint pulls that model via `ollama pull` before serving, so `ollama list` inside the container includes it and the healthcheck can pass

### Requirement: Chunk writes always record embedding_model
The system SHALL provide a `ChunkWriter` that inserts `chunks` rows using the `embedding_model` name returned by the configured `EmbeddingProvider`, so no code path can insert a chunk without recording which model embedded it.

#### Scenario: chunk-writer-records-embedding-model
- **Given** a `ChunkWriter` constructed with a stub `EmbeddingProvider` returning a known model name and a fake Postgres connection
- **When** `write(entity_id, source_id, text, metadata)` is called
- **Then** exactly one `chunks` row is inserted with `embedding` set from the provider's vector and `embedding_model` set to the provider's returned model name, never `NULL` and never caller-supplied
