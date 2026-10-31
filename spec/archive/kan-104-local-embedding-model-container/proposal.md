# KAN-104: Local embedding model container

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-104   Epic: 1 Foundation   Branch: kan-104-local-embedding-model-container

## Why
KAN-101 stood up the `embeddings` service as a bare Ollama skeleton (no model pulled) and KAN-102 added the `EmbeddingProvider` interface and its default `HTTPEmbeddingProvider`, explicitly verified only against a stubbed HTTP transport ("no live embeddings container call" — `spec/archive/kan-102-adapter-interfaces-local-implementations/verification.md`, "Not verified"). Two gaps remain before any harvester/normalizer can depend on embeddings: (1) the `embeddings` container does not actually serve a model — `ollama list` would be empty, so a real `/api/embed` call would fail; (2) there is no shared, tested code path that takes `EmbeddingProvider` output and persists a `chunks` row with `embedding_model` populated — every future harvester would otherwise re-invent this.

## What changes
- `embeddings/Dockerfile` gets an entrypoint script that pulls the configured model (`EMBEDDING_MODEL`, default `nomic-embed-text`) into the Ollama container on startup, before serving, so the container is a real local embedding service rather than an empty shell.
- `docker-compose.yml`'s `embeddings` service passes `EMBEDDING_MODEL` through so the entrypoint and the `HTTPEmbeddingProvider` agree on the model name.
- A new `adapters/chunks/writer.py` (`ChunkWriter`) that calls an injected `EmbeddingProvider`, then inserts a `chunks` row (`entity_id`, `source_id`, `text`, `embedding`, `embedding_model`, `metadata`) via an injected connection factory (same DB-API-shaped pattern as `PostgresOutboxEventBus`), so `embedding_model` is always populated from the provider's own return value, never hand-typed by a caller.
- `adapters/factory.py` gets `get_embedding_provider(...)` so future harvester/normalizer code obtains the configured `EmbeddingProvider` the same way it obtains other adapters, instead of constructing `HTTPEmbeddingProvider` directly.
- Contract tests for `ChunkWriter` against an in-memory fake Postgres connection (extending the existing `fake_postgres.py` pattern), proving `embedding_model` is always set on the inserted row and matches what the provider returned.

## In scope
- Making the `embeddings` container pull and serve one concrete local model on startup ("embedding service runs locally").
- A reusable, tested `chunks`-table write path that always records `embedding_model` ("embedding_model recorded on every chunk").
- `adapters/factory.py` wiring for `EmbeddingProvider` selection.

## Out of scope
- Any harvester or normalizer that actually produces chunk text from a source (Epic 3/5); `ChunkWriter` is infrastructure those stories will call.
- Chunk de-duplication / upsert-by-stable-key or re-harvest idempotency semantics for `chunks` (no unique key exists on `chunks` yet, and the harvester contract's "idempotent upsert keyed by external_id" applies to entities, not chunks); this story only guarantees `embedding_model` is populated on every row `ChunkWriter` inserts. Chunk identity strategy is left to the harvester epic that first needs it.
- Any change to the `chunks` table schema — `embedding_model TEXT NOT NULL` already exists from `migrations/0001_core_tables.up.sql`; no migration is added.
- Switching the default embedding model, or supporting multiple models at once.
- Cloud `EmbeddingProvider` implementations (Vertex AI, Azure AI Foundry) — local only, per `docs/ARCHITECTURE.md`.

## Acceptance criteria (from Jira)
"embedding service runs locally; embedding_model recorded on every chunk."
1. Embedding service runs locally -> scenario: embeddings-container-serves-local-model
2. `embedding_model` recorded on every chunk -> scenario: chunk-writer-records-embedding-model

## Affected
Capabilities: `spec/capabilities/foundation.md` (adds two requirements under the existing EmbeddingProvider area)   Docs/contracts: none (`chunks` schema already names `embedding_model NOT NULL`; no Confluence Contracts change needed, no new table/column, no ontology or harvester-interface change).

## Risks and open questions
- No Docker/Ollama runtime is available in this development session, so the entrypoint's `ollama pull` + serve behavior cannot be executed live here; it is verified by reading the script and by the existing `ollama list` healthcheck contract, not by a real container run. Recorded as "Not verified" in `verification.md`.
- `ChunkWriter` is verified against an in-memory fake Postgres connection (same approach KAN-102 used for `PostgresOutboxEventBus`), not a live Postgres container, for the same reason.

## Approval
Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
