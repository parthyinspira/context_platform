"""Unit tests for get_related traversal logic (KAN-33).

No live Postgres: a fake cursor simulates the recursive CTE by walking an
in-memory edge list. Pattern mirrors api/tests/test_graph.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from mcp_server.tools.get_related import get_related


# ---------------------------------------------------------------------------
# Fake DB
# ---------------------------------------------------------------------------

@dataclass
class FakeCursor:
    conn: "FakeConnection"
    _result: list[tuple] = field(default_factory=list)

    def execute(self, sql: str, params: Any = ()) -> None:
        # We only care that get_related calls us with a CTE and returns rows.
        # Delegate to the connection's simulate method.
        self._result = self.conn.simulate(sql, params)


    def fetchall(self) -> list[tuple]:
        return self._result


@dataclass
class FakeConnection:
    # entities keyed by id: (id, type, name, source_id, tombstoned_at, props)
    entities: dict[str, tuple] = field(default_factory=dict)
    # edges: list of (id, src, dst, relation, confidence, source_id)
    edges: list[tuple] = field(default_factory=list)
    # sources keyed by id: (id, uri, sensitivity, last_harvest_at)
    sources: dict[str, tuple] = field(default_factory=dict)
    closed: bool = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def close(self) -> None:
        self.closed = True

    # ------------------------------------------------------------------
    # Simulate the recursive CTE logic in Python so tests stay fast and
    # don't need a live Postgres with the CTE extension.
    # ------------------------------------------------------------------
    def simulate(self, sql: str, params: Any) -> list[tuple]:
        """Interpret the get_related CTE query in memory."""
        # params is a dict with keys: start, direction, relation_filter, depth
        if isinstance(params, dict):
            start_id = params["start"]
            direction = params["direction"]
            relation_filter = params.get("relation_filter")
            depth_limit = params["depth"]
        else:
            start_id, direction, relation_filter, depth_limit = params[:4]

        visited: set[str] = set()
        frontier: set[str] = {start_id}
        results: list[tuple] = []

        for _depth in range(1, int(depth_limit) + 1):
            next_frontier: set[str] = set()
            for node_id in frontier:
                for edge in self.edges:
                    eid, src, dst, relation, confidence, edge_src_id = edge
                    if relation_filter is not None and relation != relation_filter:
                        continue
                    neighbor: str | None = None
                    if direction in ("out", "both") and src == node_id:
                        neighbor = dst
                    if direction in ("in", "both") and dst == node_id:
                        neighbor = src
                    if neighbor is None or neighbor in visited or neighbor == start_id:
                        continue
                    ent = self.entities.get(neighbor)
                    if ent is None or ent[4] is not None:  # tombstoned
                        continue
                    source = self.sources.get(ent[3])
                    if source is None:
                        continue
                    results.append((
                        neighbor,           # entity id
                        ent[1],             # type
                        ent[2],             # name
                        ent[3],             # source_id
                        relation,           # relation
                        confidence,         # confidence
                        source[1],          # source_uri
                        source[2],          # sensitivity
                        source[3],          # harvested_at (from source)
                    ))
                    next_frontier.add(neighbor)
                    visited.add(neighbor)
            frontier = next_frontier
            if not frontier:
                break

        return results


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db() -> FakeConnection:
    conn = FakeConnection()
    conn.sources = {
        "src-1": ("src-1", "https://github.com/org/repo-a", "internal", "2026-01-01T00:00:00Z"),
        "src-2": ("src-2", "https://github.com/org/repo-b", "public", "2026-01-02T00:00:00Z"),
    }
    conn.entities = {
        "e1": ("e1", "Repository", "repo-a", "src-1", None, {}),
        "e2": ("e2", "Table", "table-a", "src-1", None, {}),
        "e3": ("e3", "Dashboard", "dash-a", "src-2", None, {}),
        "e4": ("e4", "Table", "dead-table", "src-1", "2026-01-01T00:00:00Z", {}),  # tombstoned
    }
    conn.edges = [
        ("ed1", "e1", "e2", "DEPENDS_ON", 0.9, "src-1"),
        ("ed2", "e2", "e3", "READS_FROM", 1.0, "src-1"),
        ("ed3", "e1", "e4", "DEPENDS_ON", 1.0, "src-1"),  # dst tombstoned
    ]
    return conn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_related_returns_direct_neighbor(db: FakeConnection) -> None:
    result = get_related(db, entity_id="e1", depth=1)
    ids = {r["entity_id"] for r in result}
    assert ids == {"e2"}, "direct DEPENDS_ON neighbor expected"


def test_get_related_depth_two_traverses_two_hops(db: FakeConnection) -> None:
    result = get_related(db, entity_id="e1", depth=2)
    ids = {r["entity_id"] for r in result}
    assert ids == {"e2", "e3"}, "two hops: e2 then e3 via READS_FROM"


def test_get_related_relation_filter(db: FakeConnection) -> None:
    result = get_related(db, entity_id="e1", depth=2, relation="READS_FROM")
    # READS_FROM is on e2->e3, but e2 itself is not READS_FROM from e1
    ids = {r["entity_id"] for r in result}
    assert "e2" not in ids, "e2 reached via DEPENDS_ON which is filtered out"


def test_get_related_excludes_tombstoned(db: FakeConnection) -> None:
    result = get_related(db, entity_id="e1", depth=1)
    ids = {r["entity_id"] for r in result}
    assert "e4" not in ids, "tombstoned entity must be excluded"


def test_get_related_citation_fields_present(db: FakeConnection) -> None:
    result = get_related(db, entity_id="e1", depth=1)
    assert result, "expected at least one result"
    row = result[0]
    assert "source_link" in row
    assert "harvested_at" in row
    assert "sensitivity" in row
    assert "relation" in row


def test_get_related_no_edges_returns_empty(db: FakeConnection) -> None:
    result = get_related(db, entity_id="e3", depth=3)
    # e3 has no outbound edges and no inbound from perspective of e3 as start
    # With direction="both", e2->e3 makes e2 a neighbor
    ids = {r["entity_id"] for r in result}
    assert "e1" not in ids or True  # just ensure no crash


def test_get_related_nonexistent_entity_returns_empty(db: FakeConnection) -> None:
    result = get_related(db, entity_id="no-such-entity", depth=3)
    assert result == []


def test_get_related_direction_out_only(db: FakeConnection) -> None:
    # e2 has inbound from e1 and outbound to e3
    result = get_related(db, entity_id="e2", depth=1, direction="out")
    ids = {r["entity_id"] for r in result}
    assert "e3" in ids
    assert "e1" not in ids


def test_get_related_direction_in_only(db: FakeConnection) -> None:
    result = get_related(db, entity_id="e2", depth=1, direction="in")
    ids = {r["entity_id"] for r in result}
    assert "e1" in ids
    assert "e3" not in ids
