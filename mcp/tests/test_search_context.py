"""Tests for search_context — use in-memory fakes, no live DB required."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

from search import SearchResult, search_context


# ---------------------------------------------------------------------------
# Fake cursor / connection helpers
# ---------------------------------------------------------------------------


@dataclass
class _Row:
    text: str
    uri: str
    harvested_at: datetime.datetime
    sensitivity: str

    def __iter__(self):
        return iter((self.text, self.uri, self.harvested_at, self.sensitivity))


def _make_conn(rows: list[_Row]) -> Any:
    """Return a mock psycopg-style connection whose cursor yields *rows*."""
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    cur.fetchall.return_value = [tuple(r) for r in rows]

    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

_NOW = datetime.datetime(2025, 1, 15, 12, 0, 0)


def test_search_context_returns_fields():
    """AC: each result carries source_link, harvested_at and sensitivity."""
    rows = [
        _Row("hello world chunk", "https://github.com/org/repo", _NOW, "internal"),
    ]
    conn = _make_conn(rows)
    results = search_context(conn, "hello")
    assert len(results) == 1
    r = results[0]
    assert r.text == "hello world chunk"
    assert r.source_link == "https://github.com/org/repo"
    assert r.harvested_at == _NOW.isoformat()
    assert r.sensitivity == "internal"


def test_search_context_empty_query_returns_all_up_to_limit():
    rows = [
        _Row(f"chunk {i}", "https://example.com/src", _NOW, "public")
        for i in range(10)
    ]
    conn = _make_conn(rows)
    results = search_context(conn, "", limit=5)
    # Mock returns all 10 rows (ignores LIMIT); just verify structure
    assert len(results) == 10
    assert all(isinstance(r, SearchResult) for r in results)


def test_search_context_no_results():
    conn = _make_conn([])
    results = search_context(conn, "nonexistent")
    assert results == []


def test_search_context_sql_uses_limit():
    """Verify LIMIT and ILIKE pattern are passed to the cursor."""
    conn = _make_conn([])
    search_context(conn, "foo", limit=3)
    cur = conn.cursor.return_value
    call_args = cur.execute.call_args
    sql, params = call_args[0]
    assert "%foo%" in params[0]
    assert params[1] == 3


def test_search_context_tombstoned_excluded():
    """Tombstoned entities are excluded by the SQL WHERE clause (verified via SQL content)."""
    conn = _make_conn([])
    search_context(conn, "test")
    cur = conn.cursor.return_value
    sql = cur.execute.call_args[0][0]
    assert "tombstoned_at IS NULL" in sql


def test_search_context_harvested_at_iso_format():
    """harvested_at is converted to ISO-8601 string."""
    dt = datetime.datetime(2025, 6, 1, 9, 30, 0)
    rows = [_Row("data", "https://src.example.com/repo", dt, "restricted")]
    conn = _make_conn(rows)
    results = search_context(conn, "data")
    assert results[0].harvested_at == "2025-06-01T09:30:00"
