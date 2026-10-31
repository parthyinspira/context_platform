from adapters.llm.http_llama import HTTPLLMProvider
from adapters.secret_store.env import EnvSecretStore


class StubTransport:
    def __init__(self):
        self.calls = []

    def post(self, url, json, headers):
        self.calls.append((url, json, headers))
        return {"choices": [{"message": {"content": "hi there"}}]}


def test_complete_calls_configured_endpoint_and_model(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://llama.local/v1")
    monkeypatch.setenv("LLM_API_KEY", "key-123")
    monkeypatch.setenv("LLM_MODEL_LARGE", "llama-3-70b")
    transport = StubTransport()
    provider = HTTPLLMProvider(EnvSecretStore(), transport)

    result = provider.complete([{"role": "user", "content": "hello"}])

    assert result == "hi there"
    url, body, headers = transport.calls[0]
    assert url == "http://llama.local/v1/chat/completions"
    assert body["model"] == "llama-3-70b"
    assert body["messages"] == [{"role": "user", "content": "hello"}]
    assert headers["Authorization"] == "Bearer key-123"
