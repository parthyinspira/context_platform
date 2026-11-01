from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.main import connection_factory_dependency
from app.schemas import LineageEdge, LineageNode, LineageResponse
from app.search import get_lineage

router = APIRouter()


@router.get("/lineage/{entity_id}", response_model=LineageResponse)
def get_entity_lineage(
    entity_id: str,
    direction: str = Query(default="downstream", pattern="^(upstream|downstream|both)$"),
    depth: int = Query(default=3, ge=1, le=10),
    connection_factory: Any = Depends(connection_factory_dependency),
) -> LineageResponse:
    conn = connection_factory()
    try:
        nodes, edges = get_lineage(conn, entity_id, direction, depth)
    finally:
        conn.close()
    return LineageResponse(
        root_entity_id=entity_id,
        direction=direction,
        nodes=[LineageNode(**n) for n in nodes],
        edges=[LineageEdge(**e) for e in edges],
    )
