from adapters.embedding.http_local import HTTPEmbeddingProvider
from adapters.secret_store.env import EnvSecretStore


class StubTransport:
    def __init__(self):
        self.calls = []

    def post(self, url, json):
        self.calls.append((url, json))
        return {"embeddings": [[0.1, 0.2, 0.3]]}


def test_embed_returns_vectors_and_model(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_BASE_URL", "http://embeddings:11434")
    monkeypatch.setenv("EMBEDDING_MODEL", "nomic-embed-text")
    transport = StubTransport()
    provider = HTTPEmbeddingProvider(EnvSecretStore(), transport)

    vectors, model = provider.embed(["hello"])

    assert vectors == [[0.1, 0.2, 0.3]]
    assert model == "nomic-embed-text"
    url, body = transport.calls[0]
    assert url == "http://embeddings:11434/api/embed"
    assert body == {"model": "nomic-embed-text", "input": ["hello"]}
