"""Tests for GET /entities/{id} (KAN-68). No live Postgres: an in-memory fake
stands in for `entities`/`edges`/`sources`/`chunks`/`harvest_runs`, same pattern
as `test_graph.py`.
"""
from dataclasses import dataclass, field

import pytest
from app.main import app, connection_factory_dependency
from fastapi.testclient import TestClient


@dataclass
class FakeCursor:
    conn: "FakeConnection"
    _result: list[tuple] = field(default_factory=list)

    def execute(self, sql: str, params: tuple = ()) -> None:
        sql_norm = " ".join(sql.split())

        if sql_norm.startswith("SELECT id, type, name, source_id, props FROM entities WHERE id"):
            rows = [r for r in self.conn.entities if r[0] == params[0] and r[5] is None]
            self._result = [r[:5] for r in rows]
            return

        if sql_norm.startswith("SELECT id, uri, owner FROM sources WHERE id"):
            self._result = [r for r in self.conn.sources if r[0] == params[0]]
            return

        edges_select = (
            "SELECT id, src_entity_id, dst_entity_id, relation FROM edges "
            "WHERE src_entity_id = %s OR dst_entity_id = %s"
        )
        if sql_norm.startswith(edges_select):
            self._result = [r for r in self.conn.edges if r[1] == params[0] or r[2] == params[0]]
            return

        if sql_norm.startswith("SELECT id, type, name FROM entities WHERE id = ANY"):
            wanted = set(params[0])
            self._result = [
                (r[0], r[1], r[2]) for r in self.conn.entities if r[0] in wanted and r[5] is None
            ]
            return

        if sql_norm.startswith("SELECT id, harvested_at FROM chunks WHERE entity_id"):
            rows = [r for r in self.conn.chunks if r[2] == params[0]]
            self._result = [(r[0], r[1]) for r in rows]
            return

        if sql_norm.startswith("SELECT id, started_at FROM harvest_runs WHERE source_id"):
            rows = [r for r in self.conn.harvest_runs if r[2] == params[0]]
            self._result = [(r[0], r[1]) for r in sorted(rows, key=lambda r: r[1], reverse=True)]
            return

        raise AssertionError(f"unexpected SQL: {sql_norm}")

    def fetchone(self) -> tuple | None:
        return self._result[0] if self._result else None

    def fetchall(self) -> list[tuple]:
        return self._result


@dataclass
class FakeConnection:
    # entities: (id, type, name, source_id, props, tombstoned_at)
    entities: list[tuple] = field(default_factory=list)
    # edges: (id, src, dst, relation)
    edges: list[tuple] = field(default_factory=list)
    # sources: (id, uri, owner)
    sources: list[tuple] = field(default_factory=list)
    # chunks: (id, harvested_at, entity_id)
    chunks: list[tuple] = field(default_factory=list)
    # harvest_runs: (id, started_at, source_id)
    harvest_runs: list[tuple] = field(default_factory=list)
    closed: bool = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def conn():
    c = FakeConnection()
    c.entities = [
        ("e1", "Repository", "repo-a", "src-1", {"language": "python"}, None),
        ("e2", "Table", "table-a", "src-1", {}, None),
        ("e3", "Service", "svc-a", "src-1", {}, None),
        ("e4", "Repository", "tombstoned-repo", "src-1", {}, "2026-01-01T00:00:00Z"),
    ]
    c.edges = [
        ("ed1", "e1", "e2", "DEPENDS_ON"),
        ("ed2", "e3", "e1", "CONTAINS"),
    ]
    c.sources = [("src-1", "https://github.com/acme/repo-a", "alice@acme.com")]
    c.chunks = [
        ("c1", "2026-02-01T00:00:00Z", "e1"),
    ]
    c.harvest_runs = [
        ("run-early", "2026-01-15T00:00:00Z", "src-1"),
        ("run-latest", "2026-02-02T00:00:00Z", "src-1"),
    ]
    return c


@pytest.fixture
def client(conn):
    app.dependency_overrides[connection_factory_dependency] = lambda: (lambda: conn)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_entity_returns_props_edges_grouped_citations_owner(client, conn) -> None:
    response = client.get("/entities/e1")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "e1"
    assert body["props"] == {"language": "python"}
    assert body["owner"] == "alice@acme.com"
    assert body["source_uri"] == "https://github.com/acme/repo-a"

    assert set(body["edges_by_relation"].keys()) == {"DEPENDS_ON", "CONTAINS"}
    depends_on = body["edges_by_relation"]["DEPENDS_ON"]
    assert depends_on == [
        {
            "id": "ed1",
            "direction": "out",
            "entity_id": "e2",
            "entity_type": "Table",
            "entity_name": "table-a",
        }
    ]
    contains = body["edges_by_relation"]["CONTAINS"]
    assert contains == [
        {
            "id": "ed2",
            "direction": "in",
            "entity_id": "e3",
            "entity_type": "Service",
            "entity_name": "svc-a",
        }
    ]

    assert body["citations"] == [
        {
            "source_link": "https://github.com/acme/repo-a",
            "harvested_at": "2026-02-01T00:00:00Z",
            "run_id": "run-early",
        }
    ]
    assert conn.closed is True


def test_entity_citation_run_id_null_when_no_run_matches(client, conn) -> None:
    conn.harvest_runs = [("run-after", "2026-03-01T00:00:00Z", "src-1")]

    response = client.get("/entities/e1")

    assert response.status_code == 200
    assert response.json()["citations"][0]["run_id"] is None


def test_entity_not_found_returns_404(client) -> None:
    response = client.get("/entities/does-not-exist")

    assert response.status_code == 404


def test_entity_tombstoned_returns_404(client) -> None:
    response = client.get("/entities/e4")

    assert response.status_code == 404
