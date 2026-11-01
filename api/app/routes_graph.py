"""Graph query route (KAN-58): nodes/edges from `entities`/`edges`, filtered."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.main import connection_factory_dependency
from app.schemas_graph import GraphEdgeOut, GraphNodeOut, GraphOut

router = APIRouter()


@router.get("/graph", response_model=GraphOut)
def query_graph(
    source_id: str | None = None,
    type: str | None = None,
    relation: str | None = None,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> GraphOut:
    conn = connection_factory()
    try:
        cur = conn.cursor()

        node_sql = (
            "SELECT id, type, name, source_id, props FROM entities WHERE tombstoned_at IS NULL"
        )
        node_params: list[Any] = []
        if source_id is not None:
            node_sql += " AND source_id = %s"
            node_params.append(source_id)
        if type is not None:
            node_sql += " AND type = %s"
            node_params.append(type)
        cur.execute(node_sql, tuple(node_params))
        node_rows = cur.fetchall()
        nodes = [
            GraphNodeOut(id=str(r[0]), type=r[1], name=r[2], source_id=str(r[3]), props=r[4] or {})
            for r in node_rows
        ]
        node_ids = {n.id for n in nodes}

        edge_sql = (
            "SELECT id, src_entity_id, dst_entity_id, relation, confidence, source_id FROM edges"
        )
        edge_clauses: list[str] = []
        edge_params: list[Any] = []
        if source_id is not None:
            edge_clauses.append("source_id = %s")
            edge_params.append(source_id)
        if relation is not None:
            edge_clauses.append("relation = %s")
            edge_params.append(relation)
        if edge_clauses:
            edge_sql += " WHERE " + " AND ".join(edge_clauses)
        cur.execute(edge_sql, tuple(edge_params))
        edge_rows = cur.fetchall()
        edges = [
            GraphEdgeOut(
                id=str(r[0]),
                src_entity_id=str(r[1]),
                dst_entity_id=str(r[2]),
                relation=r[3],
                confidence=r[4],
                source_id=str(r[5]),
            )
            for r in edge_rows
            if str(r[1]) in node_ids and str(r[2]) in node_ids
        ]
    finally:
        conn.close()

    return GraphOut(nodes=nodes, edges=edges)
