"""Tests for POST /sources/test-connection, POST /sources/{id}/discover and
POST /sources/{id}/plan (KAN-58). No live Postgres: DB access is overridden with
an in-memory fake, same pattern as `test_sources.py`.
"""
from dataclasses import dataclass, field
from typing import Any

import pytest
from app.main import app, connection_factory_dependency
from fastapi.testclient import TestClient

import fixtures_harvesters  # noqa: F401 - registers api-test-* harvester types


@dataclass
class FakeCursor:
    conn: "FakeConnection"
    _result: tuple | None = None

    def execute(self, sql: str, params: tuple = ()) -> None:
        sql_norm = " ".join(sql.split())
        if sql_norm.startswith("SELECT id, type, uri FROM sources WHERE id = %s"):
            (source_id,) = params
            row = self.conn.sources.get(source_id)
            self._result = row
            return
        raise AssertionError(f"unexpected SQL: {sql_norm}")

    def fetchone(self) -> tuple | None:
        return self._result


@dataclass
class FakeConnection:
    sources: dict[str, tuple] = field(default_factory=dict)

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        pass

    def close(self) -> None:
        pass


@pytest.fixture
def conn():
    return FakeConnection()


@pytest.fixture
def client(conn):
    app.dependency_overrides[connection_factory_dependency] = lambda: (lambda: conn)
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- POST /sources/test-connection ---


def test_connection_ok(client) -> None:
    response = client.post(
        "/sources/test-connection",
        json={"type": "api-test-ok", "uri": "https://example/repo.git"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "error": None}


def test_connection_failure_returns_error_without_echoing_credentials(client) -> None:
    response = client.post(
        "/sources/test-connection",
        json={
            "type": "api-test-connect-fail",
            "uri": "https://example/repo.git",
            "credentials_ref": "super-secret-token",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {"ok": False, "error": "bad credentials"}
    assert "super-secret-token" not in response.text


# --- POST /sources/{id}/discover ---


def test_discover_returns_scope_tree(client, conn) -> None:
    conn.sources["src-1"] = ("src-1", "api-test-ok", "https://example/repo.git")

    response = client.post("/sources/src-1/discover")

    assert response.status_code == 200
    body = response.json()
    assert body["roots"][0]["id"] == "obj-1"
    assert body["roots"][0]["size_hint"] == 100


def test_discover_unknown_source_returns_404(client) -> None:
    response = client.post("/sources/missing/discover")
    assert response.status_code == 404


# --- POST /sources/{id}/plan ---


def test_plan_returns_estimates_from_profile(client, conn) -> None:
    conn.sources["src-1"] = ("src-1", "api-test-ok", "https://example/repo.git")

    response = client.post("/sources/src-1/plan", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["object_count"] == 1
    assert body["estimated_bytes"] == 100
    assert body["estimated_files"] == 1
    assert body["budget_warnings"] == []


def test_plan_reports_budget_warning_when_estimate_exceeds_budget(client, conn) -> None:
    conn.sources["src-1"] = ("src-1", "api-test-tight-budget", "https://example/repo.git")

    response = client.post("/sources/src-1/plan", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["plan"]["budgets"]["max_bytes"] == 5
    assert any("max_bytes" in w for w in body["budget_warnings"])
