"""Tests for GET /lineage/{entity_id} (KAN-48).

No live Postgres: a fake cursor intercepts the recursive-CTE query and returns
pre-configured rows. The fake simulates the EXISTS check for the start entity
and then the lineage CTE result.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from app.main import app, connection_factory_dependency
from fastapi.testclient import TestClient

# Columns returned by the lineage CTE:
# ent.id, ent.type, ent.name, ent.source_id, ent.props,
# edge_id, src_entity_id, dst_entity_id, relation, confidence,
# depth, source_uri, sensitivity, harvested_at


def _lineage_row(
    ent_id: str,
    ent_type: str,
    name: str,
    source_id: str,
    edge_id: str,
    src_entity_id: str,
    dst_entity_id: str,
    relation: str,
    confidence: float,
    depth: int,
    source_uri: str = "https://example.com",
    sensitivity: str = "internal",
    harvested_at: str | None = "2026-01-01T00:00:00Z",
) -> tuple:
    return (
        ent_id, ent_type, name, source_id, {},
        edge_id, src_entity_id, dst_entity_id, relation, confidence,
        depth, source_uri, sensitivity, harvested_at,
    )


@dataclass
class FakeCursor:
    conn: "FakeConnection"
    _result: list[tuple] = field(default_factory=list)

    def execute(self, sql: str, params: object = ()) -> None:
        sql_norm = " ".join(sql.split())
        if "tombstoned_at IS NULL" in sql_norm and "FROM entities WHERE id" in sql_norm:
            # Start-entity existence check
            entity_id = params[0] if isinstance(params, (list, tuple)) else params["start_id"]
            self._result = [
                (r,) for r in self.conn.live_entity_ids if r == str(entity_id)
            ]
            return
        if "WITH RECURSIVE lineage" in sql_norm:
            self._result = self.conn.lineage_rows
            return
        self._result = []

    def fetchone(self) -> tuple | None:
        return self._result[0] if self._result else None

    def fetchall(self) -> list[tuple]:
        return list(self._result)


@dataclass
class FakeConnection:
    live_entity_ids: list[str] = field(default_factory=list)
    lineage_rows: list[tuple] = field(default_factory=list)
    closed: bool = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def client_factory():
    def _make(conn: FakeConnection) -> TestClient:
        app.dependency_overrides[connection_factory_dependency] = lambda: (lambda: conn)
        return TestClient(app)

    yield _make
    app.dependency_overrides.clear()


# --- R1: downstream traversal ---

def test_downstream_returns_job_and_dashboard(client_factory) -> None:
    """table → job → dashboard: get_lineage(table, downstream, 3) returns both."""
    conn = FakeConnection(
        live_entity_ids=["table-1"],
        lineage_rows=[
            _lineage_row("job-1", "Job", "etl-job", "src-1", "ed1", "job-1", "table-1", "READS_FROM", 1.0, 1),
            _lineage_row("dash-1", "Dashboard", "my-dash", "src-1", "ed2", "dash-1", "job-1", "DERIVED_FROM", 0.9, 2),
        ],
    )
    client = client_factory(conn)
    resp = client.get("/lineage/table-1", params={"direction": "downstream", "depth": 3})
    assert resp.status_code == 200
    body = resp.json()
    node_ids = {n["id"] for n in body["nodes"]}
    assert node_ids == {"job-1", "dash-1"}
    edge_ids = {e["id"] for e in body["edges"]}
    assert edge_ids == {"ed1", "ed2"}
    assert body["direction"] == "downstream"


# --- R1: upstream traversal ---

def test_upstream_returns_table_for_job(client_factory) -> None:
    """job reads from table: get_lineage(job, upstream) returns table."""
    conn = FakeConnection(
        live_entity_ids=["job-1"],
        lineage_rows=[
            _lineage_row("table-1", "Table", "orders", "src-1", "ed1", "job-1", "table-1", "READS_FROM", 1.0, 1),
        ],
    )
    client = client_factory(conn)
    resp = client.get("/lineage/job-1", params={"direction": "upstream", "depth": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert [n["id"] for n in body["nodes"]] == ["table-1"]
    assert body["direction"] == "upstream"


# --- R2: citations present ---

def test_lineage_nodes_include_citations(client_factory) -> None:
    conn = FakeConnection(
        live_entity_ids=["table-1"],
        lineage_rows=[
            _lineage_row(
                "job-1", "Job", "etl", "src-1", "ed1", "job-1", "table-1", "READS_FROM", 1.0, 1,
                source_uri="https://github.com/org/repo",
                sensitivity="internal",
                harvested_at="2026-10-01T00:00:00Z",
            ),
        ],
    )
    client = client_factory(conn)
    resp = client.get("/lineage/table-1")
    assert resp.status_code == 200
    node = resp.json()["nodes"][0]
    assert node["source_link"] == "https://github.com/org/repo"
    assert node["sensitivity"] == "internal"
    assert node["harvested_at"] == "2026-10-01T00:00:00Z"


# --- R3: tombstoned entity → 404 for start; excluded from traversal ---

def test_returns_404_when_start_entity_tombstoned(client_factory) -> None:
    conn = FakeConnection(live_entity_ids=[], lineage_rows=[])
    client = client_factory(conn)
    resp = client.get("/lineage/tombstoned-entity-1")
    assert resp.status_code == 404


def test_tombstoned_entity_not_in_lineage_results(client_factory) -> None:
    """CTE excludes tombstoned entities; fake returns empty rows to simulate this."""
    conn = FakeConnection(
        live_entity_ids=["table-1"],
        lineage_rows=[],  # tombstoned job excluded by the CTE JOIN condition
    )
    client = client_factory(conn)
    resp = client.get("/lineage/table-1")
    assert resp.status_code == 200
    assert resp.json()["nodes"] == []


# --- edge cases ---

def test_depth_out_of_range_returns_422(client_factory) -> None:
    conn = FakeConnection(live_entity_ids=["e1"], lineage_rows=[])
    client = client_factory(conn)
    assert client.get("/lineage/e1", params={"depth": 0}).status_code == 422
    assert client.get("/lineage/e1", params={"depth": 11}).status_code == 422


def test_no_downstream_returns_empty_nodes(client_factory) -> None:
    conn = FakeConnection(live_entity_ids=["e1"], lineage_rows=[])
    client = client_factory(conn)
    resp = client.get("/lineage/e1")
    assert resp.status_code == 200
    assert resp.json()["nodes"] == []
    assert resp.json()["edges"] == []
