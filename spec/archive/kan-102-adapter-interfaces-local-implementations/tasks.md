# Tasks

- [x] 1. Add migration `migrations/0002_outbox_events.up.sql` / `.down.sql` for the `outbox_events` table (id, topic, payload jsonb, created_at, delivered_at nullable) (scenario: eventbus-publish-and-poll) - test first: contract test against a real/ test Postgres if available, else unit test on the SQL shape
- [x] 2. Add `adapters/event_bus/base.py` (`EventBus` interface) and `adapters/event_bus/postgres_outbox.py` (default impl) + contract tests (scenario: eventbus-publish-and-poll)
- [x] 3. Add `adapters/object_store/base.py` (`ObjectStore` interface) and `adapters/object_store/local.py` (default impl) + contract tests (scenario: objectstore-put-get-list-delete)
- [x] 4. Add `adapters/secret_store/base.py` (`SecretStore` interface) and `adapters/secret_store/env.py` (default impl) + contract tests (scenario: secretstore-env-get)
- [x] 5. Add `adapters/llm/base.py` (`LLMProvider` interface) and `adapters/llm/http_llama.py` (default impl, injectable HTTP transport) + contract test against a stub transport (scenario: llmprovider-interface-shape)
- [x] 6. Add `adapters/embedding/base.py` (`EmbeddingProvider` interface) and `adapters/embedding/http_local.py` (default impl, injectable HTTP transport) + contract test against a stub transport (scenario: embeddingprovider-interface-shape)
- [x] 7. Add `adapters/factory.py` selecting each implementation from `.env` keys (`EVENT_BUS`, `OBJECT_STORE`, `SECRET_STORE`, `LLM_PROVIDER`, `EMBEDDING_PROVIDER`)
- [x] 8. Add a repo-wide cloud-SDK-import scan test/script and run it (scenario: no-cloud-sdk-outside-adapters)
- [x] 9. Run `contract-check` and `secret-scan` skills
- [x] 10. `verification.md` completed with evidence per scenario
