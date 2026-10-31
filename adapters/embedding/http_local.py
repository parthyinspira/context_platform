from typing import Any, Protocol

from adapters.secret_store.base import SecretStore

from .base import EmbeddingProvider


class HTTPTransport(Protocol):
    def post(self, url: str, json: dict[str, Any]) -> Any: ...


class HTTPEmbeddingProvider(EmbeddingProvider):
    """Default EmbeddingProvider: the local `embeddings` container (Ollama-compatible HTTP API).

    `transport` is injectable so tests never make a real network call.
    """

    def __init__(self, secret_store: SecretStore, transport: HTTPTransport):
        self._secrets = secret_store
        self._transport = transport

    def embed(self, texts: list[str]) -> tuple[list[list[float]], str]:
        base_url = self._secrets.get("EMBEDDING_BASE_URL")
        model = self._secrets.get("EMBEDDING_MODEL")
        payload = {"model": model, "input": texts}
        response = self._transport.post(f"{base_url}/api/embed", json=payload)
        return response["embeddings"], model
