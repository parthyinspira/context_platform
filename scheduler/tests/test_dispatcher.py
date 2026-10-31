"""Tests for POST /sources/{id}/run and GET /sources/due. No live Postgres is used:
the DB connection and the EventBus are overridden with in-memory fakes via FastAPI
dependency overrides, so these tests exercise the routes' SQL/response wiring and
due-source logic without infra.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from app.main import app, connection_factory_dependency, event_bus_dependency
from fastapi.testclient import TestClient


@dataclass
class FakeCursor:
    conn: "FakeConnection"
    _result: Any = None
    _results: list = field(default_factory=list)

    def execute(self, sql: str, params: tuple = ()) -> None:
        sql_norm = " ".join(sql.split())
        if sql_norm.startswith("SELECT id, type, uri, status FROM sources"):
            (source_id,) = params
            source = self.conn.sources.get(source_id)
            self._result = (
                (source["id"], source["type"], source["uri"], source["status"])
                if source
                else None
            )
        elif sql_norm.startswith("INSERT INTO dispatcher_runs"):
            (source_id,) = params
            run_id = str(uuid.uuid4())
            self.conn.runs.append({"id": run_id, "source_id": source_id, "status": "queued"})
            self._result = (run_id, source_id, "queued")
        elif sql_norm.startswith("SELECT id, type, uri, schedule, last_harvest_at FROM sources"):
            self._results = [
                (s["id"], s["type"], s["uri"], s["schedule"], s["last_harvest_at"])
                for s in self.conn.sources.values()
                if s["status"] == "active"
            ]
        else:
            raise AssertionError(f"unexpected SQL: {sql_norm}")

    def fetchone(self) -> Any:
        return self._result

    def fetchall(self) -> list:
        return self._results


@dataclass
class FakeConnection:
    sources: dict
    runs: list = field(default_factory=list)
    committed: bool = False
    closed: bool = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

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


def _source(**overrides) -> dict:
    base = {
        "id": str(uuid.uuid4()),
        "type": "git_repo",
        "uri": "https://github.com/example/repo.git",
        "schedule": "0 * * * *",
        "status": "active",
        "last_harvest_at": None,
    }
    base.update(overrides)
    return base


@pytest.fixture
def make_client():
    def _make(sources: dict):
        conn = FakeConnection(sources=sources)
        bus = FakeEventBus()
        app.dependency_overrides[connection_factory_dependency] = lambda: (lambda: conn)
        app.dependency_overrides[event_bus_dependency] = lambda: bus
        return TestClient(app), conn, bus

    yield _make
    app.dependency_overrides.clear()


def test_run_active_source_queues_run_and_publishes_event(make_client) -> None:
    source = _source()
    client, conn, bus = make_client({source["id"]: source})

    response = client.post(f"/sources/{source['id']}/run")

    assert response.status_code == 201
    body = response.json()
    assert body["source_id"] == source["id"]
    assert body["status"] == "queued"
    assert "id" in body and body["id"]

    assert len(conn.runs) == 1
    assert conn.committed is True
    assert conn.closed is True

    assert len(bus.published) == 1
    topic, payload = bus.published[0]
    assert topic == "harvest.requested"
    assert payload["run_id"] == body["id"]
    assert payload["source_id"] == source["id"]
    assert payload["source_type"] == "git_repo"


def test_run_unknown_source_returns_404(make_client) -> None:
    client, conn, bus = make_client({})

    response = client.post(f"/sources/{uuid.uuid4()}/run")

    assert response.status_code == 404
    assert conn.runs == []
    assert bus.published == []


def test_run_inactive_source_returns_409(make_client) -> None:
    source = _source(status="paused")
    client, conn, bus = make_client({source["id"]: source})

    response = client.post(f"/sources/{source['id']}/run")

    assert response.status_code == 409
    assert conn.runs == []
    assert bus.published == []


def test_due_sources_includes_never_harvested_active_source(make_client) -> None:
    source = _source(last_harvest_at=None)
    client, _, _ = make_client({source["id"]: source})

    response = client.get("/sources/due")

    assert response.status_code == 200
    ids = [s["id"] for s in response.json()]
    assert source["id"] in ids


def test_due_sources_excludes_recently_harvested_source(make_client) -> None:
    source = _source(
        schedule="0 0 1 1 *",  # yearly: not due again right after harvesting
        last_harvest_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    client, _, _ = make_client({source["id"]: source})

    response = client.get("/sources/due")

    assert response.status_code == 200
    ids = [s["id"] for s in response.json()]
    assert source["id"] not in ids


def test_due_sources_includes_source_past_its_schedule(make_client) -> None:
    source = _source(
        schedule="*/5 * * * *",
        last_harvest_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    client, _, _ = make_client({source["id"]: source})

    response = client.get("/sources/due")

    assert response.status_code == 200
    ids = [s["id"] for s in response.json()]
    assert source["id"] in ids


def test_due_sources_excludes_inactive_sources(make_client) -> None:
    source = _source(status="paused", last_harvest_at=None)
    client, _, _ = make_client({source["id"]: source})

    response = client.get("/sources/due")

    assert response.status_code == 200
    assert response.json() == []
