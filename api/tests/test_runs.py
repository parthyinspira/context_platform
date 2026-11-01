"""Tests for POST /sources/{id}/runs, GET /runs/{id}, PATCH /runs/{id}/stop and
GET /runs/{id}/validation (KAN-58). No live Postgres: an in-memory fake stands in
for `harvest_runs`/`sources`, same pattern as `test_sources.py`.
"""
import json
import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest
from app.main import app, connection_factory_dependency
from fastapi.testclient import TestClient


@dataclass
class FakeCursor:
    conn: "FakeConnection"
    _result: Any = None

    def execute(self, sql: str, params: tuple = ()) -> None:
        sql_norm = " ".join(sql.split())

        if sql_norm.startswith("SELECT id FROM sources WHERE id = %s"):
            (source_id,) = params
            self._result = (source_id,) if source_id in self.conn.sources else None
            return

        if sql_norm.startswith("INSERT INTO harvest_runs"):
            source_id, plan_json = params
            run_id = str(uuid.uuid4())
            self.conn.runs[run_id] = {
                "id": run_id,
                "source_id": source_id,
                "state": "APPROVED",
                "plan": json.loads(plan_json),
                "manifest": {},
                "error": None,
                "report": None,
            }
            self._result = (run_id, source_id, "APPROVED")
            return

        if sql_norm.startswith("SELECT id, source_id, state, plan, manifest, error, report"):
            (run_id,) = params
            run = self.conn.runs.get(run_id)
            self._result = _run_tuple(run) if run else None
            return

        if sql_norm.startswith("UPDATE harvest_runs SET state = 'FAILED'"):
            error, run_id = params
            run = self.conn.runs[run_id]
            run["state"] = "FAILED"
            run["error"] = error
            self._result = _run_tuple(run)
            return

        raise AssertionError(f"unexpected SQL: {sql_norm}")

    def fetchone(self) -> Any:
        return self._result


def _run_tuple(run: dict) -> tuple:
    return (run["id"], run["source_id"], run["state"], run["plan"], run["manifest"],
            run["error"], run["report"])


@dataclass
class FakeConnection:
    sources: set[str] = field(default_factory=set)
    runs: dict[str, dict] = field(default_factory=dict)

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        pass

    def close(self) -> None:
        pass


@pytest.fixture
def conn():
    c = FakeConnection()
    c.sources.add("src-1")
    return c


@pytest.fixture
def client(conn):
    app.dependency_overrides[connection_factory_dependency] = lambda: (lambda: conn)
    yield TestClient(app)
    app.dependency_overrides.clear()


VALID_PLAN = {"plan": {"include": [], "exclude": [], "size_cap_bytes": None, "budgets": {}}}


def test_create_run_then_get_returns_detail(client, conn) -> None:
    create = client.post("/sources/src-1/runs", json=VALID_PLAN)
    assert create.status_code == 201
    run_id = create.json()["id"]
    assert create.json()["state"] == "APPROVED"

    detail = client.get(f"/runs/{run_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["source_id"] == "src-1"
    assert body["manifest_summary"] == {
        "discovered": 0, "fetched": 0, "skipped": 0, "failed": 0, "fetched_bytes": 0,
    }


def test_get_run_sums_fetched_bytes_and_lists_log_entries(client, conn) -> None:
    run_id = client.post("/sources/src-1/runs", json=VALID_PLAN).json()["id"]
    conn.runs[run_id]["manifest"] = {
        "entries": [
            {"ref": "a.py", "outcome": "fetched", "size_bytes": 100, "outcome_reason": "fetched ok"},
            {"ref": "b.py", "outcome": "fetched", "size_bytes": 50, "outcome_reason": "fetched ok"},
            {"ref": "c.py", "outcome": "skipped", "size_bytes": 10, "outcome_reason": "excluded"},
        ]
    }

    response = client.get(f"/runs/{run_id}")

    body = response.json()
    assert body["manifest_summary"]["fetched_bytes"] == 150
    assert [e["ref"] for e in body["log_entries"]] == ["a.py", "b.py", "c.py"]
    assert body["log_entries"][2]["outcome"] == "skipped"


def test_create_run_unknown_source_returns_404(client) -> None:
    response = client.post("/sources/missing/runs", json=VALID_PLAN)
    assert response.status_code == 404


def test_stop_nonterminal_run_sets_failed(client, conn) -> None:
    run_id = client.post("/sources/src-1/runs", json=VALID_PLAN).json()["id"]
    conn.runs[run_id]["state"] = "HARVESTING"

    response = client.patch(f"/runs/{run_id}/stop")

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "FAILED"
    assert body["error"] == "stopped by user"


def test_stop_terminal_run_returns_409(client, conn) -> None:
    run_id = client.post("/sources/src-1/runs", json=VALID_PLAN).json()["id"]
    conn.runs[run_id]["state"] = "PUBLISHED"

    response = client.patch(f"/runs/{run_id}/stop")

    assert response.status_code == 409


def test_get_validation_report_present(client, conn) -> None:
    run_id = client.post("/sources/src-1/runs", json=VALID_PLAN).json()["id"]
    conn.runs[run_id]["report"] = {
        "status": "WARN",
        "checks": [
            {"name": "completeness", "status": "WARN", "message": "ok-ish",
             "counts": {"fetched": 9}, "samples": ["a.txt"]}
        ],
    }

    response = client.get(f"/runs/{run_id}/validation")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "WARN"
    assert body["checks"][0]["samples"] == ["a.txt"]


def test_get_validation_report_missing_returns_404(client, conn) -> None:
    run_id = client.post("/sources/src-1/runs", json=VALID_PLAN).json()["id"]

    response = client.get(f"/runs/{run_id}/validation")

    assert response.status_code == 404
