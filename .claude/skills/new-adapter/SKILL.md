---
name: new-adapter
description: Scaffold or extend a cloud-portability adapter (EventBus, ObjectStore, SecretStore, LLMProvider, EmbeddingProvider) with a shared contract test. Use whenever an adapter or a new provider implementation is added.
---

Adapters live under `adapters/` (follow the repo layout). Business logic depends only on the interfaces; cloud SDK imports are allowed only inside `adapters/`.

1. Interface: small and cloud-neutral (for example `EventBus.publish(topic, payload)` / `subscribe(topic, handler)`; `ObjectStore.put/get/list/delete`; `SecretStore.get(key)`; `LLMProvider.complete(...)` with tool-calling and structured output; `EmbeddingProvider.embed(texts)` returning the model name).
2. Local default implementation first: Postgres outbox, local folder/MinIO, env/Docker secrets, Llama endpoint from `.env`, local embedding model.
3. Contract test suite shared by every implementation (the same tests run against each adapter); cloud implementations (Pub/Sub, GCS, Secret Manager, Vertex AI, Service Bus, Blob, Key Vault, Azure AI Foundry) are added later and must pass the same suite.
4. Selection through configuration (`.env` keys such as `EVENT_BUS`, `OBJECT_STORE`, `SECRET_STORE`, `LLM_PROVIDER`, `EMBEDDING_PROVIDER`); add the key to `.env.example`.
5. Never log secret values or payload contents that may be sensitive.
6. Update `docs/ARCHITECTURE.md` (portability table) if a provider is added, and run `contract-check`.
