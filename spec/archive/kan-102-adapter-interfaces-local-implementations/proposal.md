# KAN-102: Adapter interfaces with local implementations

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-102   Epic: 1 Foundation   Branch: kan-102-adapter-interfaces-local-implementations

## Why
`CLAUDE.md` and `docs/ARCHITECTURE.md` require every cloud-touching concern (events, object storage, secrets, LLM, embeddings) to sit behind a small interface so business logic never imports a cloud SDK directly and the same images can run on local Docker, GCP and Azure. KAN-101 built the compose skeletons and already reserved `.env.example` keys (`EVENT_BUS`, `OBJECT_STORE`, `OBJECT_STORE_PATH`, `SECRET_STORE`, `LLM_PROVIDER`, `EMBEDDING_PROVIDER`) for this story but no `adapters/` package exists yet. This story adds the five interfaces and their local/default implementations so later stories (source registry, harvesters, ontology updater) can depend on the interfaces only.

## What changes
- Add an `adapters/` Python package (used by `api` and `scheduler`) with five interfaces and local default implementations:
  - `EventBus` — Postgres outbox (`publish`, `subscribe`/`poll`), backed by a new `outbox_events` table (migration).
  - `ObjectStore` — local filesystem folder under `OBJECT_STORE_PATH` (`put`, `get`, `list`, `delete`).
  - `SecretStore` — environment variables (`get`).
  - `LLMProvider` — interface only plus a Llama/OpenAI-compatible HTTP implementation reading `LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL_*` from `.env` via `SecretStore`.
  - `EmbeddingProvider` — interface only plus a local implementation calling the `embeddings` container's OpenAI/Ollama-compatible embeddings endpoint (`EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`).
- A shared contract test suite per interface (`adapters/tests/contract/`) that every implementation (current and future cloud ones) must pass.
- A factory/selector (`adapters/factory.py`) that reads `.env` keys (`EVENT_BUS`, `OBJECT_STORE`, `SECRET_STORE`, `LLM_PROVIDER`, `EMBEDDING_PROVIDER`) and returns the configured implementation.
- A new migration adding the `outbox_events` table used by the Postgres-outbox `EventBus`.
- `contract-check`-clean: no cloud SDK imports anywhere outside `adapters/`.

## In scope
- The five interfaces and their local/default implementations named in the AC.
- Contract tests for each interface, run against the local implementation.
- `outbox_events` migration.
- Wiring `api`'s dependencies to add `adapters/` as an importable package (requirements only if a new library is needed, e.g. `httpx` for the LLM/embedding HTTP calls).

## Out of scope
- Cloud adapter implementations (Pub/Sub, Service Bus, GCS, Blob Storage, Secret Manager, Key Vault, Vertex AI, Azure AI Foundry, Anthropic) — later stories per `docs/ARCHITECTURE.md` portability table.
- MinIO container / switching `ObjectStore` default to MinIO — AC says "local/MinIO"; the local filesystem implementation satisfies the default, MinIO is a future selectable implementation behind the same interface, not required to exist yet.
- Actually publishing/consuming domain events (`source.registered`, `harvest.completed`, `ontology.updated`) — that is Epic 2+ business logic; this story only provides the `EventBus` mechanism.
- Dispatcher/scheduler behaviour, source registry routes, harvester or ontology code.
- Real LLM/embedding calls in tests (network calls); contract tests use a stub/fake HTTP server or mock transport, not a live model.

## Acceptance criteria (from Jira)
"EventBus (Postgres outbox), ObjectStore (local/MinIO), SecretStore (env), LLMProvider, EmbeddingProvider; no cloud SDK imports outside adapters/."
1. `EventBus` interface with a Postgres-outbox implementation -> scenario: eventbus-publish-and-poll
2. `ObjectStore` interface with a local implementation -> scenario: objectstore-put-get-list-delete
3. `SecretStore` interface with an env implementation -> scenario: secretstore-env-get
4. `LLMProvider` interface (with a default implementation) -> scenario: llmprovider-interface-shape
5. `EmbeddingProvider` interface (with a default implementation) -> scenario: embeddingprovider-interface-shape
6. No cloud SDK imports outside `adapters/` -> scenario: no-cloud-sdk-outside-adapters

## Affected
Capabilities: `spec/capabilities/foundation.md` (adds adapter requirements)   Docs/contracts: `docs/ARCHITECTURE.md` (portability table already names these interfaces, no change needed), `.env.example` (no new keys needed, already reserved in KAN-101), new migration `migrations/0002_outbox_events.{up,down}.sql`.

## Risks and open questions
- No live Llama endpoint or embeddings model is available in this session; `LLMProvider`/`EmbeddingProvider` local implementations are verified against a stubbed HTTP transport, not a real model call. Noted as not verified end-to-end.
- `ObjectStore` AC says "local/MinIO" — only the local filesystem implementation is built now; a MinIO implementation is deferred as it is not required for the compose stack today (no MinIO container in KAN-101).

## Approval
Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
