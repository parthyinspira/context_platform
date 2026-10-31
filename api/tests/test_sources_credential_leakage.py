"""Regression test: even when `credentials_ref` matches a real, resolvable
secret value in the SecretStore, that value must never appear in the
POST /sources request/response cycle or in any captured log line. The API
only ever stores/returns the reference key (see KAN-7, KAN-10).
"""
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.main import app, connection_factory_dependency, event_bus_dependency
from fastapi.testclient import TestClient


@dataclass
class FakeSourcesCursor:
    conn: "FakeSourcesConnection"
    _result: tuple | None = None

    def execute(self, sql: str, params: tuple) -> None:
        type_, uri, schedule, credentials_ref, owner, sensitivity = params
        source_id = str(uuid.uuid4())
        self.conn.inserted.append({"credentials_ref": credentials_ref})
        self._result = (
            source_id,
            type_,
            uri,
            schedule,
            credentials_ref,
            owner,
            sensitivity,
            "active",
        )

    def fetchone(self) -> tuple:
        return self._result


@dataclass
class FakeSourcesConnection:
    inserted: list[dict] = field(default_factory=list)

    def cursor(self) -> FakeSourcesCursor:
        return FakeSourcesCursor(self)

    def commit(self) -> None:
        pass

    def close(self) -> None:
        pass


@dataclass
class FakeEventBus:
    published: list[tuple[str, dict]] = field(default_factory=list)

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.published.append((topic, payload))

    def poll(self, topic: str, limit: int = 10) -> list:
        return []


def test_real_secret_value_never_appears_in_response_or_logs(monkeypatch, caplog) -> None:
    secret_value = "sk-live-super-secret-do-not-leak"
    monkeypatch.setenv("GIT_REPO_TOKEN_REF", secret_value)

    conn = FakeSourcesConnection()
    bus = FakeEventBus()
    app.dependency_overrides[connection_factory_dependency] = lambda: (lambda: conn)
    app.dependency_overrides[event_bus_dependency] = lambda: bus
    try:
        client = TestClient(app)
        payload = {
            "type": "git_repo",
            "uri": "https://github.com/example/repo.git",
            "schedule": "0 * * * *",
            "credentials_ref": "GIT_REPO_TOKEN_REF",
            "owner": "platform-team",
            "sensitivity": "internal",
        }
        with caplog.at_level(logging.DEBUG):
            response = client.post("/sources", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert secret_value not in response.text
    body = response.json()
    assert body["credentials_ref"] == "GIT_REPO_TOKEN_REF"

    for record in caplog.records:
        assert secret_value not in record.getMessage()
