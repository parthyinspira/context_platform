"""Tests for POST /sources. No live Postgres is used: the DB connection and the
EventBus are overridden with in-memory fakes via FastAPI dependency overrides, so
these tests exercise validation and the route's SQL/response wiring without infra.
"""
import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest
from app.main import app, connection_factory_dependency, event_bus_dependency
from fastapi.testclient import TestClient


@dataclass
class _Row:
    data: dict


@dataclass
class FakeSourcesCursor:
    conn: "FakeSourcesConnection"
    _result: tuple | None = None

    def execute(self, sql: str, params: tuple) -> None:
        sql_norm = " ".join(sql.split())
        assert sql_norm.startswith("INSERT INTO sources"), f"unexpected SQL: {sql_norm}"
        type_, uri, schedule, credentials_ref, owner, sensitivity = params
        source_id = str(uuid.uuid4())
        self.conn.inserted.append(
            {
                "id": source_id,
                "type": type_,
                "uri": uri,
                "schedule": schedule,
                "credentials_ref": credentials_ref,
                "owner": owner,
                "sensitivity": sensitivity,
                "status": "active",
            }
        )
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
    committed: bool = False
    closed: bool = False

    def cursor(self) -> FakeSourcesCursor:
        return FakeSourcesCursor(self)

    def commit(self) -> None:
        self.committed = True

    def close(self) -> None:
        self.closed = True


@dataclass
class FakeEventBus:
    published: list[tuple[str, dict]] = field(default_factory=list)

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.published.append((topic, payload))

    def poll(self, topic: str, limit: int = 10) -> list:
        return []


VALID_PAYLOAD = {
    "type": "git_repo",
    "uri": "https://github.com/example/repo.git",
    "schedule": "0 * * * *",
    "credentials_ref": "git-repo-token",
    "owner": "platform-team",
    "sensitivity": "internal",
}


@pytest.fixture
def fakes():
    conn = FakeSourcesConnection()
    bus = FakeEventBus()
    app.dependency_overrides[connection_factory_dependency] = lambda: (lambda: conn)
    app.dependency_overrides[event_bus_dependency] = lambda: bus
    yield conn, bus
    app.dependency_overrides.clear()


@pytest.fixture
def client(fakes):
    return TestClient(app)


def test_register_a_source_stores_active_row_and_returns_id(fakes, client) -> None:
    conn, bus = fakes
    response = client.post("/sources", json=VALID_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert "id" in body and body["id"]
    assert body["status"] == "active"
    assert body["credentials_ref"] == "git-repo-token"

    assert len(conn.inserted) == 1
    assert conn.inserted[0]["status"] == "active"
    assert conn.committed is True
    assert conn.closed is True

    assert bus.published == [("source.registered", {"id": body["id"]})]


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("type", ""),
        ("uri", ""),
        ("credentials_ref", ""),
        ("owner", ""),
    ],
)
def test_reject_blank_required_fields(fakes, client, field_name, bad_value) -> None:
    conn, _ = fakes
    payload = {**VALID_PAYLOAD, field_name: bad_value}
    response = client.post("/sources", json=payload)
    assert response.status_code == 422
    assert conn.inserted == []


@pytest.mark.parametrize(
    "bad_schedule",
    ["", "not a cron", "* * * *", "0 0 0 0 0 0", "* * * * * *"],
)
def test_reject_invalid_schedule(fakes, client, bad_schedule) -> None:
    conn, _ = fakes
    payload = {**VALID_PAYLOAD, "schedule": bad_schedule}
    response = client.post("/sources", json=payload)
    assert response.status_code == 422
    assert conn.inserted == []


def test_reject_invalid_sensitivity(fakes, client) -> None:
    conn, _ = fakes
    payload = {**VALID_PAYLOAD, "sensitivity": "top-secret"}
    response = client.post("/sources", json=payload)
    assert response.status_code == 422
    assert conn.inserted == []


def test_reject_missing_field(fakes, client) -> None:
    conn, _ = fakes
    payload = dict(VALID_PAYLOAD)
    del payload["owner"]
    response = client.post("/sources", json=payload)
    assert response.status_code == 422
    assert conn.inserted == []


@pytest.mark.parametrize(
    "schedule", ["0 * * * *", "*/15 * * * *", "0 0 1 1 *", "0,30 9-17 * * 1-5"]
)
def test_accepts_valid_cron_schedules(fakes, client, schedule) -> None:
    payload = {**VALID_PAYLOAD, "schedule": schedule}
    response = client.post("/sources", json=payload)
    assert response.status_code == 201
