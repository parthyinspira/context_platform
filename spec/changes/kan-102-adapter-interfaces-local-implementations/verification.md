# Verification

Status: PASS
Date: 2026-10-30   Commit: 0291e9d903aa8d360fbcfc0885e48b907d04a043 (working tree on top of it)

## Checks
| Check | Result |
|---|---|
| Lint | No linter configured in the repo; none run |
| Tests (`adapters/`) | `python -m pytest adapters/tests -q` -> 9/9 passed |
| Regression (`api`, `scheduler`) | `pytest` run from within each service dir (existing pattern) -> 1/1 each passed; unaffected by this change |
| contract-check | No schema table/column edits outside the new `outbox_events` migration; no new ontology types; no harvester or MCP code touched; scanned diff for `google.cloud`/`azure`/`boto3` outside `adapters/` -> none found |
| secret-scan | `git ls-files \| grep -E '\.env($\|\.)'` -> only `.env.example`; diff scanned for key/token/password patterns -> none found |
| Definition of Done | All tasks ticked |

## Scenario evidence
| Requirement / Scenario | Evidence | Result |
|---|---|---|
| EventBus Postgres outbox / eventbus-publish-and-poll | `adapters/tests/contract/test_event_bus.py::test_publish_and_poll_returns_event_once` and `::test_poll_respects_topic_and_limit`, against `PostgresOutboxEventBus` driven by an in-memory fake DB-API connection (`fake_postgres.py`) implementing the exact SQL the adapter issues against the new `outbox_events` table | PASS (not run against a live Postgres container — see Not verified) |
| ObjectStore local / objectstore-put-get-list-delete | `adapters/tests/contract/test_object_store.py::test_put_get_list_delete` (put/list/get/delete round trip on a temp dir) and `::test_key_cannot_escape_root` (path traversal guard) | PASS |
| SecretStore env / secretstore-env-get | `adapters/tests/contract/test_secret_store.py` — set/get round trip and missing-key returns `None` | PASS |
| LLMProvider / llmprovider-interface-shape | `adapters/tests/contract/test_llm_provider.py::test_complete_calls_configured_endpoint_and_model` against a stub HTTP transport, asserting configured base URL, model and bearer token are used | PASS (no live Llama endpoint call — see Not verified) |
| EmbeddingProvider / embeddingprovider-interface-shape | `adapters/tests/contract/test_embedding_provider.py::test_embed_returns_vectors_and_model` against a stub HTTP transport | PASS (no live embeddings container call — see Not verified) |
| No cloud SDK outside adapters / no-cloud-sdk-outside-adapters | `adapters/tests/test_no_cloud_sdk_outside_adapters.py` AST-scans `api/`, `ui/`, `scheduler/`, `embeddings/`, `migrations/`, `scripts/` for `google.cloud`, `boto3`, `azure`, `anthropic`, `openai` imports; manual `grep -rn "google.cloud\|^import azure\|boto3" --include="*.py" . \| grep -v /adapters/` also returned no matches | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| EventBus (Postgres outbox) | eventbus-publish-and-poll | PASS (fake-DB tested, not live Postgres) |
| ObjectStore (local/MinIO) | objectstore-put-get-list-delete | PASS for local; MinIO implementation deliberately out of scope (see proposal.md) |
| SecretStore (env) | secretstore-env-get | PASS |
| LLMProvider | llmprovider-interface-shape | PASS (stub transport, not a live Llama call) |
| EmbeddingProvider | embeddingprovider-interface-shape | PASS (stub transport, not a live embeddings call) |
| No cloud SDK imports outside adapters/ | no-cloud-sdk-outside-adapters | PASS |

## Not verified
- **Live Postgres**: `PostgresOutboxEventBus` is exercised against an in-memory fake connection that mimics the exact SQL statements it issues, not a real Postgres server. The migration SQL (`migrations/0002_outbox_events.up.sql`) was not run against a live `postgres` container in this session (no Docker/Postgres available here). Risk is low — the SQL mirrors the style of the existing `migrations/0001_core_tables.up.sql`, which was verified live in KAN-101 — but this specific table has not been.
- **Live LLM / embeddings calls**: `HTTPLLMProvider` and `HTTPEmbeddingProvider` are verified against injected stub transports only; no real Llama endpoint or `embeddings` (Ollama) container was called, since no `LLM_BASE_URL`/running embeddings container is available in this session.
- **MinIO**: not implemented (see proposal.md "Out of scope"); only the local-filesystem `ObjectStore` implementation exists.
