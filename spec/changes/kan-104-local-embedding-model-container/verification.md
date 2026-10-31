# Verification

Status: PASS
Date: 2026-10-30   Commit: e0e3815982038b77ee68867f49f4111253d38394 (working tree on top of it)

## Checks
| Check | Result |
|---|---|
| Lint (`ruff check adapters embeddings`) | All checks passed |
| Tests (`python -m pytest adapters -q`) | 14/14 passed (5 new: `test_write_records_embedding_model_from_provider`, `test_write_never_lets_caller_set_embedding_model`, `test_write_defaults_metadata_to_empty_dict`, `test_factory_selects_local_http_provider`, `test_factory_rejects_unknown_provider`) |
| Regression (`api`, `scheduler`) | `pytest` in each service dir -> 1/1 passed each, unaffected by this change |
| contract-check | No `chunks` schema/column edit (it already had `embedding_model TEXT NOT NULL` from `migrations/0001_core_tables.up.sql`); no new migration needed or added; no ontology types touched; no harvester or MCP code touched; `ChunkWriter`/`get_embedding_provider` follow the existing adapter pattern; scanned new/changed files for `google.cloud`/`azure`/`boto3` -> none found |
| secret-scan | `git ls-files \| grep -E '\.env($\|\.)'` -> only `.env.example`; new/changed files scanned for key/token/password/connection-string patterns -> none found |
| Definition of Done | All tasks ticked |

## Scenario evidence
| Requirement / Scenario | Evidence | Result |
|---|---|---|
| Embeddings container serves a local model / embeddings-container-serves-local-model | `embeddings/entrypoint.sh` starts `ollama serve`, polls `ollama list` until the server responds, then runs `ollama pull "$EMBEDDING_MODEL"` before waiting on the server process; `embeddings/Dockerfile` sets `ENV EMBEDDING_MODEL=nomic-embed-text`, copies the script as `ENTRYPOINT`, and the `HEALTHCHECK` now asserts `ollama list \| grep -q "$EMBEDDING_MODEL"` instead of just `ollama list`; `docker-compose.yml`'s `embeddings` service passes `EMBEDDING_MODEL` from `.env` (already `nomic-embed-text` in `.env.example`), matching `HTTPEmbeddingProvider`'s default | PASS by inspection (not run against a live container — see Not verified) |
| Chunk writes always record embedding_model / chunk-writer-records-embedding-model | `adapters/tests/contract/test_chunk_writer.py::test_write_records_embedding_model_from_provider` inserts via `PostgresChunkWriter` against `FakeChunksConnection` and asserts the inserted row's `embedding_model` equals the stub `EmbeddingProvider`'s returned model name and is never empty; `::test_write_never_lets_caller_set_embedding_model` asserts `ChunkWriter.write`'s signature has no `embedding_model` parameter at all, so it can only come from the provider; `::test_write_defaults_metadata_to_empty_dict` covers the no-metadata case | PASS (fake-DB tested, not a live Postgres — see Not verified) |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Embedding service runs locally | embeddings-container-serves-local-model | PASS (entrypoint verified by inspection; no Docker runtime available in this session to run it live) |
| embedding_model recorded on every chunk | chunk-writer-records-embedding-model | PASS (fake-DB tested) |

## Not verified
- **Live Ollama container**: no Docker runtime is available in this development session, so `embeddings/entrypoint.sh` pulling `nomic-embed-text` and serving `/api/embed` was not exercised against a real `ollama/ollama` container. The script was reviewed for correctness (wait-for-server loop before `ollama pull`, `ENTRYPOINT` wired, healthcheck updated) but not run live.
- **Live Postgres**: `PostgresChunkWriter` is exercised against an in-memory fake connection (`FakeChunksConnection`) that mimics the exact SQL it issues against the `chunks` table, not a real Postgres server, for the same reason `PostgresOutboxEventBus` was verified this way in KAN-102.
- **End-to-end wiring into a harvester/normalizer**: no harvester or normalizer exists yet to call `ChunkWriter` from real harvested content (Epic 3/5, out of scope for this story per `proposal.md`).
