# Capability: foundation

### Requirement: EventBus interface with Postgres outbox default
The system SHALL provide an `EventBus` interface (`publish(topic, payload)`, `poll(topic, limit)` or `subscribe`) with a default implementation backed by a Postgres `outbox_events` table, selected via `.env` key `EVENT_BUS=postgres_outbox`.

#### Scenario: eventbus-publish-and-poll
- **Given** a Postgres-outbox `EventBus` instance and an empty `outbox_events` table
- **When** `publish("source.registered", {...})` is called and then the topic is polled
- **Then** the published event is returned exactly once per consumer cursor, with its topic and payload intact

### Requirement: ObjectStore interface with local filesystem default
The system SHALL provide an `ObjectStore` interface (`put`, `get`, `list`, `delete`) with a default implementation that stores objects under a local folder (`OBJECT_STORE_PATH`), selected via `.env` key `OBJECT_STORE=local`.

#### Scenario: objectstore-put-get-list-delete
- **Given** a local-filesystem `ObjectStore` rooted at a temp directory
- **When** an object is put under a key, then listed, then got, then deleted
- **Then** `list` shows the key after `put`, `get` returns the exact bytes written, and the key is absent from `list` after `delete`

### Requirement: SecretStore interface with env default
The system SHALL provide a `SecretStore` interface (`get(key)`) with a default implementation that reads from process environment variables, selected via `.env` key `SECRET_STORE=env`.

#### Scenario: secretstore-env-get
- **Given** an environment variable is set and an env-backed `SecretStore`
- **When** `get(key)` is called for that variable's name
- **Then** the stored value is returned, and `get` for a missing key returns `None` without raising

### Requirement: LLMProvider interface
The system SHALL provide an `LLMProvider` interface (`complete(messages, **options)`) with a default HTTP implementation that reads its endpoint and model from `.env` via `SecretStore`, selected via `.env` key `LLM_PROVIDER=llama`.

#### Scenario: llmprovider-interface-shape
- **Given** an `LLMProvider` implementation configured against a stub HTTP transport
- **When** `complete(messages)` is called
- **Then** the implementation sends the configured model and messages to the configured base URL and returns the stub's response text, without importing any cloud-specific SDK

### Requirement: EmbeddingProvider interface
The system SHALL provide an `EmbeddingProvider` interface (`embed(texts) -> (vectors, model_name)`) with a default HTTP implementation that reads its endpoint and model from `.env`, selected via `.env` key `EMBEDDING_PROVIDER=local`.

#### Scenario: embeddingprovider-interface-shape
- **Given** an `EmbeddingProvider` implementation configured against a stub HTTP transport
- **When** `embed(["hello"])` is called
- **Then** the implementation returns one vector per input text and the configured `embedding_model` name, without importing any cloud-specific SDK

### Requirement: No cloud SDK imports outside adapters
Business logic (everything outside `adapters/`) SHALL NOT import a cloud provider SDK (for example `google-cloud-*`, `azure-*`, `boto3`, `anthropic`, `openai` used directly for a cloud-hosted model) directly; only code under `adapters/` may do so.

#### Scenario: no-cloud-sdk-outside-adapters
- **Given** the full repository source tree
- **When** it is scanned for cloud SDK import statements outside `adapters/`
- **Then** no matches are found

### Requirement: Lint and test CI
The repository SHALL run lint and automated tests on every push and pull request against `main` via a CI workflow, covering the Python services (`api`, `scheduler`, `adapters`) and the UI service, plus a Linux `docker compose up` smoke test.

#### Scenario: ci-lint-runs
- **Given** a pull request with a Python lint violation in `api/`, `scheduler/`, or `adapters/`
- **When** the CI workflow runs
- **Then** the lint job fails, blocking a clean CI run

#### Scenario: ci-test-runs
- **Given** a pull request that changes `api/`, `scheduler/`, `adapters/`, or `ui/`
- **When** the CI workflow runs
- **Then** `pytest` runs for each Python service's `tests/` directory, `node --test` runs for `ui/test`, and the workflow fails if any test fails

#### Scenario: ci-compose-smoke-linux
- **Given** the CI workflow running on an `ubuntu-latest` runner
- **When** the compose-smoke-test job runs `docker compose up`
- **Then** all services reach healthy and each documented `/health` endpoint responds, closing the KAN-101 Linux verification gap

### Requirement: Project documentation entry point
`CLAUDE.md` SHALL document the system architecture, ontology v0 (entities and relations) and the harvester interface, kept in sync with the current repository state.

#### Scenario: claude-md-documents-contracts
- **Given** `CLAUDE.md` in the repository root
- **When** it is read
- **Then** it describes the container architecture, lists the ontology v0 entity and relation types, and gives the `Harvester` interface (`discover`, `fetch`, `normalize`)

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
