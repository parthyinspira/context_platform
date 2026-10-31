# Tasks

- [x] 1. Add `embeddings/entrypoint.sh` that starts `ollama serve` in the background, waits for it, runs `ollama pull "$EMBEDDING_MODEL"`, then waits on the server process; update `embeddings/Dockerfile` to use it as `ENTRYPOINT` (scenario: embeddings-container-serves-local-model)
- [x] 2. Pass `EMBEDDING_MODEL` through to the `embeddings` service in `docker-compose.yml` (scenario: embeddings-container-serves-local-model)
- [x] 3. Add `adapters/chunks/base.py` (`ChunkWriter` constructor contract) and `adapters/chunks/writer.py` (default implementation) using an injected `EmbeddingProvider` and DB-API connection factory, test first (scenario: chunk-writer-records-embedding-model)
- [x] 4. Extend `adapters/tests/contract/fake_postgres.py` (or add a small chunks-specific fake) to support `INSERT INTO chunks ...` and add `adapters/tests/contract/test_chunk_writer.py` (scenario: chunk-writer-records-embedding-model)
- [x] 5. Add `get_embedding_provider` to `adapters/factory.py`
- [x] 6. Run `contract-check` and `secret-scan` skills
- [x] 7. `verification.md` completed with evidence per scenario
