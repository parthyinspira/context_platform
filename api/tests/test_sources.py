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


def _row_tuple(row: dict) -> tuple:
    return (
        row["id"],
        row["type"],
        row["uri"],
        row["schedule"],
        row["credentials_ref"],
        row["owner"],
        row["sensitivity"],
        row["status"],
    )


@dataclass
class FakeSourcesCursor:
    conn: "FakeSourcesConnection"
    _result: tuple | None = None
    _results: list[tuple] = field(default_factory=list)

    def execute(self, sql: str, params: tuple = ()) -> None:
        sql_norm = " ".join(sql.split())

        if sql_norm.startswith("INSERT INTO sources"):
            type_, uri, schedule, credentials_ref, owner, sensitivity = params
            source_id = str(uuid.uuid4())
            row = {
                "id": source_id,
                "type": type_,
                "uri": uri,
                "schedule": schedule,
                "credentials_ref": credentials_ref,
                "owner": owner,
                "sensitivity": sensitivity,
                "status": "active",
            }
            self.conn.rows[source_id] = row
            self.conn.inserted.append(row)
            self._result = _row_tuple(row)
            return

        if sql_norm.startswith("SELECT") and "WHERE id = %s" in sql_norm:
            (source_id,) = params
            row = self.conn.rows.get(source_id)
            self._result = _row_tuple(row) if row else None
            return

        if sql_norm.startswith("SELECT") and "FROM sources ORDER BY id" in sql_norm:
            self._results = [
                _row_tuple(row) for _, row in sorted(self.conn.rows.items())
            ]
            return

        if sql_norm.startswith("UPDATE sources SET schedule = %s, status = %s"):
            schedule, status, source_id = params
            row = self.conn.rows.get(source_id)
            if row is None:
                self._result = None
                return
            row = {**row, "schedule": schedule, "status": status}
            self.conn.rows[source_id] = row
            self._result = _row_tuple(row)
            return

        if sql_norm.startswith("UPDATE sources SET status = 'disabled'"):
            (source_id,) = params
            row = self.conn.rows.get(source_id)
            if row is None:
                self._result = None
                return
            row = {**row, "status": "disabled"}
            self.conn.rows[source_id] = row
            self._result = _row_tuple(row)
            return

        raise AssertionError(f"unexpected SQL: {sql_norm}")

    def fetchone(self) -> tuple | None:
        return self._result

    def fetchall(self) -> list[tuple]:
        return self._results


@dataclass
class FakeSourcesConnection:
    rows: dict[str, dict] = field(default_factory=dict)
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


# --- GET /sources (scenario: list-sources) ---


def test_list_sources_returns_all_rows(fakes, client) -> None:
    conn, _ = fakes
    client.post("/sources", json=VALID_PAYLOAD)
    client.post("/sources", json={**VALID_PAYLOAD, "uri": "https://github.com/example/other.git"})

    response = client.get("/sources")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {row["uri"] for row in body} == {
        VALID_PAYLOAD["uri"],
        "https://github.com/example/other.git",
    }
    for row in body:
        assert row["credentials_ref"] == "git-repo-token"


def test_list_sources_empty(fakes, client) -> None:
    response = client.get("/sources")
    assert response.status_code == 200
    assert response.json() == []


# --- PATCH /sources/{id} (scenarios: patch-schedule, patch-status,
# patch-invalid-schedule, patch-invalid-status, patch-unknown-source) ---


def test_patch_updates_schedule(fakes, client) -> None:
    source_id = client.post("/sources", json=VALID_PAYLOAD).json()["id"]

    response = client.patch(f"/sources/{source_id}", json={"schedule": "0 0 * * *"})

    assert response.status_code == 200
    body = response.json()
    assert body["schedule"] == "0 0 * * *"
    assert body["status"] == "active"
    assert body["uri"] == VALID_PAYLOAD["uri"]


def test_patch_updates_status(fakes, client) -> None:
    source_id = client.post("/sources", json=VALID_PAYLOAD).json()["id"]

    response = client.patch(f"/sources/{source_id}", json={"status": "disabled"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "disabled"
    assert body["schedule"] == VALID_PAYLOAD["schedule"]


def test_patch_rejects_invalid_schedule(fakes, client) -> None:
    conn, _ = fakes
    source_id = client.post("/sources", json=VALID_PAYLOAD).json()["id"]

    response = client.patch(f"/sources/{source_id}", json={"schedule": "not a cron"})

    assert response.status_code == 422
    assert conn.rows[source_id]["schedule"] == VALID_PAYLOAD["schedule"]


def test_patch_rejects_invalid_status(fakes, client) -> None:
    conn, _ = fakes
    source_id = client.post("/sources", json=VALID_PAYLOAD).json()["id"]

    response = client.patch(f"/sources/{source_id}", json={"status": "archived"})

    assert response.status_code == 422
    assert conn.rows[source_id]["status"] == "active"


def test_patch_unknown_source_returns_404(fakes, client) -> None:
    conn, _ = fakes

    response = client.patch(f"/sources/{uuid.uuid4()}", json={"status": "disabled"})

    assert response.status_code == 404
    assert conn.rows == {}


# --- DELETE /sources/{id} (scenarios: delete-soft-disables, delete-unknown-source) ---


def test_delete_soft_disables_source(fakes, client) -> None:
    conn, _ = fakes
    source_id = client.post("/sources", json=VALID_PAYLOAD).json()["id"]

    response = client.delete(f"/sources/{source_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "disabled"
    assert source_id in conn.rows
    assert conn.rows[source_id]["status"] == "disabled"


def test_delete_unknown_source_returns_404(fakes, client) -> None:
    response = client.delete(f"/sources/{uuid.uuid4()}")
    assert response.status_code == 404
