"""Unit tests for hybrid search, sensitivity filtering, lineage traversal."""
from unittest.mock import MagicMock

from app.search import get_lineage, hybrid_search


def test_hybrid_search_returns_empty_when_no_results():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchall.return_value = []
    cur.fetchone.return_value = None
    results = hybrid_search(conn, "test query")
    assert results == []


def test_hybrid_search_sensitivity_filter_passes_param():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchall.side_effect = [[], []]
    cur.fetchone.return_value = None
    results = hybrid_search(conn, "query", sensitivities=["public"])
    assert results == []
    call_args_list = cur.execute.call_args_list
    assert any("sensitivity" in str(c) for c in call_args_list)


def test_hybrid_search_tombstone_join_present():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchall.side_effect = [
        [("chunk-1", 1)],
        [],
        [],
    ]
    cur.fetchone.return_value = ("chunk-1", b"\x00" * 16)
    hybrid_search(conn, "test")
    detail_calls = [c for c in cur.execute.call_args_list if "tombstoned_at IS NULL" in str(c)]
    assert len(detail_calls) >= 1


def test_hybrid_search_result_has_citation_fields():
    import datetime

    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    chunk_id = "cid-1"
    # keyword fetchall → 1 result; fetchone for embedding → None (skip vector);
    # detail fetchall → full row
    cur.fetchall.side_effect = [
        [(chunk_id, 1)],
        [
            (
                chunk_id,
                "some text",
                datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
                "eid-1",
                "Table",
                "my_table",
                "https://github.com/org/repo",
                "public",
            )
        ],
    ]
    cur.fetchone.return_value = None  # no embedding → skip vector search

    results = hybrid_search(conn, "some")
    assert len(results) == 1
    r = results[0]
    assert r["source_link"] == "https://github.com/org/repo"
    assert r["sensitivity"] == "public"
    assert "harvested_at" in r
    assert r["score"] > 0


def test_lineage_downstream_bfs():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    table_id = "entity-table"
    job_id = "entity-job"
    dash_id = "entity-dash"

    cur.fetchone.side_effect = [
        (table_id, "Table", "orders"),
        (job_id, "Job", "etl_job"),
        (dash_id, "Dashboard", "sales_dash"),
    ]
    cur.fetchall.side_effect = [
        [("e1", table_id, job_id, "READS_FROM", 0.9)],
        [("e2", job_id, dash_id, "WRITES_TO", 0.8)],
        [],
    ]

    nodes, edges = get_lineage(conn, table_id, "downstream", 3)
    node_ids = [n["entity_id"] for n in nodes]
    assert table_id in node_ids
    assert job_id in node_ids
    assert dash_id in node_ids
    assert len(edges) == 2


def test_lineage_respects_depth_limit():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    e1, e2, e3 = "e1", "e2", "e3"
    cur.fetchone.side_effect = [
        (e1, "Table", "t1"),
        (e2, "Job", "j1"),
    ]
    cur.fetchall.side_effect = [
        [("edge1", e1, e2, "READS_FROM", 0.9)],
        [],
    ]
    nodes, edges = get_lineage(conn, e1, "downstream", 1)
    node_ids = [n["entity_id"] for n in nodes]
    assert e1 in node_ids
    assert e2 in node_ids
    assert e3 not in node_ids


def test_lineage_excludes_tombstoned_entities():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    e1, e2 = "e1", "e2"
    cur.fetchone.side_effect = [
        (e1, "Table", "t1"),
        None,
    ]
    cur.fetchall.side_effect = [
        [("edge1", e1, e2, "READS_FROM", 0.9)],
        [],
    ]
    nodes, edges = get_lineage(conn, e1, "downstream", 3)
    node_ids = [n["entity_id"] for n in nodes]
    assert e1 in node_ids
    assert e2 not in node_ids


def test_health_endpoint(app_with_mock_conn):
    client, _ = app_with_mock_conn
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_search_endpoint_requires_q(app_with_mock_conn):
    client, _ = app_with_mock_conn
    resp = client.get("/search")
    assert resp.status_code == 422


def test_search_endpoint_empty_results(app_with_mock_conn):
    client, mock_conn = app_with_mock_conn
    cur = MagicMock()
    mock_conn.cursor.return_value = cur
    cur.fetchall.side_effect = [[], []]
    cur.fetchone.return_value = None
    resp = client.get("/search?q=hello")
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []
    assert data["total"] == 0


def test_search_endpoint_filters_propagated(app_with_mock_conn):
    client, mock_conn = app_with_mock_conn
    cur = MagicMock()
    mock_conn.cursor.return_value = cur
    cur.fetchall.side_effect = [[], []]
    cur.fetchone.return_value = None
    resp = client.get("/search?q=test&sensitivities=public&entity_types=Table")
    assert resp.status_code == 200
    sql_calls = [str(c) for c in cur.execute.call_args_list]
    assert any("sensitivity" in s for s in sql_calls)
    assert any("type" in s for s in sql_calls)
