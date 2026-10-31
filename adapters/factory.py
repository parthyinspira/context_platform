"""Select the configured adapter implementation for each interface from `.env` keys.

Business logic should obtain adapters through this module rather than importing a
concrete implementation directly, so swapping `.env` selects a different backend
(for example a future `EVENT_BUS=pubsub`) without code changes.
"""
from typing import Any

from adapters.embedding.base import EmbeddingProvider
from adapters.embedding.http_local import HTTPEmbeddingProvider
from adapters.event_bus.base import EventBus
from adapters.event_bus.postgres_outbox import PostgresOutboxEventBus
from adapters.object_store.base import ObjectStore
from adapters.object_store.local import LocalObjectStore
from adapters.secret_store.base import SecretStore
from adapters.secret_store.env import EnvSecretStore


def get_secret_store(secret_store: str | None = None) -> SecretStore:
    kind = secret_store or EnvSecretStore().get("SECRET_STORE") or "env"
    if kind == "env":
        return EnvSecretStore()
    raise ValueError(f"unknown SECRET_STORE: {kind}")


def get_object_store(secrets: SecretStore, object_store: str | None = None) -> ObjectStore:
    kind = object_store or secrets.get("OBJECT_STORE") or "local"
    if kind == "local":
        return LocalObjectStore(secrets.get("OBJECT_STORE_PATH") or "./local-data/objects")
    raise ValueError(f"unknown OBJECT_STORE: {kind}")


def get_event_bus(
    connection_factory: Any, secrets: SecretStore, event_bus: str | None = None
) -> EventBus:
    kind = event_bus or secrets.get("EVENT_BUS") or "postgres_outbox"
    if kind == "postgres_outbox":
        return PostgresOutboxEventBus(connection_factory)
    raise ValueError(f"unknown EVENT_BUS: {kind}")


def get_embedding_provider(
    secrets: SecretStore, transport: Any, embedding_provider: str | None = None
) -> EmbeddingProvider:
    kind = embedding_provider or secrets.get("EMBEDDING_PROVIDER") or "local"
    if kind == "local":
        return HTTPEmbeddingProvider(secrets, transport)
    raise ValueError(f"unknown EMBEDDING_PROVIDER: {kind}")
