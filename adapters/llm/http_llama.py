from typing import Any, Protocol

from adapters.secret_store.base import SecretStore

from .base import LLMProvider


class HTTPTransport(Protocol):
    def post(self, url: str, json: dict[str, Any], headers: dict[str, str]) -> Any: ...


class HTTPLLMProvider(LLMProvider):
    """Default LLMProvider: an OpenAI-compatible HTTP endpoint (Meta Llama hackathon credits).

    `transport` is injectable so tests never make a real network call; production code
    passes an `httpx`-backed transport, kept inside this adapter module only.
    """

    def __init__(self, secret_store: SecretStore, transport: HTTPTransport, model_key: str = "LLM_MODEL_LARGE"):
        self._secrets = secret_store
        self._transport = transport
        self._model_key = model_key

    def complete(self, messages: list[dict[str, str]], **options: Any) -> str:
        base_url = self._secrets.get("LLM_BASE_URL")
        api_key = self._secrets.get("LLM_API_KEY")
        model = self._secrets.get(self._model_key)
        response = self._transport.post(
            f"{base_url}/chat/completions",
            json={"model": model, "messages": messages, **options},
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )
        return response["choices"][0]["message"]["content"]
