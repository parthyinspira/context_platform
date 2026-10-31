"""Tests for GET /graph (KAN-58). No live Postgres: an in-memory fake stands in
for `entities`/`edges`, same pattern as `test_sources.py`.
"""
from dataclasses import dataclass, field
from typing import Any

import pytest
from app.main import app, connection_factory_dependency
from fastapi.testclient import TestClient


@dataclass
class FakeCursor:
    conn: "FakeConnection"
    _result: list[tuple] = field(default_factory=list)

    def execute(self, sql: str, params: tuple = ()) -> None:
        sql_norm = " ".join(sql.split())
        if sql_norm.startswith("SELECT id, type, name, source_id, props FROM entities"):
            rows = [r for r in self.conn.entities if r[5] is None]  # tombstoned_at IS NULL
            idx = 0
            if "source_id = %s" in sql_norm:
                rows = [r for r in rows if r[3] == params[idx]]
                idx += 1
            if "type = %s" in sql_norm:
                rows = [r for r in rows if r[1] == params[idx]]
                idx += 1
            self._result = [r[:5] for r in rows]
            return
        if sql_norm.startswith("SELECT id, src_entity_id, dst_entity_id, relation, confidence, source_id FROM edges"):
            rows = list(self.conn.edges)
            idx = 0
            if "source_id = %s" in sql_norm:
                rows = [r for r in rows if r[5] == params[idx]]
                idx += 1
            if "relation = %s" in sql_norm:
                rows = [r for r in rows if r[3] == params[idx]]
                idx += 1
            self._result = rows
            return
        raise AssertionError(f"unexpected SQL: {sql_norm}")

    def fetchall(self) -> list[tuple]:
        return self._result


@dataclass
class FakeConnection:
    entities: list[tuple] = field(default_factory=list)  # (id, type, name, source_id, props, tombstoned_at)
    edges: list[tuple] = field(default_factory=list)  # (id, src, dst, relation, confidence, source_id)

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)


@pytest.fixture
def conn():
    c = FakeConnection()
    c.entities = [
        ("e1", "Repository", "repo-a", "src-1", {}, None),
        ("e2", "Table", "table-a", "src-1", {}, None),
        ("e3", "Repository", "repo-b", "src-2", {}, None),
        ("e4", "Repository", "tombstoned-repo", "src-1", {}, "2026-01-01T00:00:00Z"),
    ]
    c.edges = [
        ("ed1", "e1", "e2", "DEPENDS_ON", 1.0, "src-1"),
        ("ed2", "e1", "e4", "DEPENDS_ON", 1.0, "src-1"),  # dst is tombstoned, excluded from result
    ]
    return c


@pytest.fixture
def client(conn):
    app.dependency_overrides[connection_factory_dependency] = lambda: (lambda: conn)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_graph_filters_by_source_and_type(client) -> None:
    response = client.get("/graph", params={"source_id": "src-1", "type": "Repository"})

    assert response.status_code == 200
    body = response.json()
    assert [n["id"] for n in body["nodes"]] == ["e1"]


def test_graph_excludes_tombstoned_entities_and_their_edges(client) -> None:
    response = client.get("/graph", params={"source_id": "src-1"})

    assert response.status_code == 200
    body = response.json()
    node_ids = {n["id"] for n in body["nodes"]}
    assert node_ids == {"e1", "e2"}
    assert [e["id"] for e in body["edges"]] == ["ed1"]
