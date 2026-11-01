from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.main import connection_factory_dependency
from app.schemas import SearchResponse, SearchResult
from app.search import hybrid_search

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
def search_context(
    q: str = Query(..., min_length=1),
    source_ids: list[str] | None = Query(default=None),
    entity_types: list[str] | None = Query(default=None),
    sensitivities: list[str] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    connection_factory: Any = Depends(connection_factory_dependency),
) -> SearchResponse:
    conn = connection_factory()
    try:
        rows = hybrid_search(
            conn,
            q,
            source_ids=source_ids,
            entity_types=entity_types,
            sensitivities=sensitivities,
            limit=limit,
        )
    finally:
        conn.close()
    results = [SearchResult(**r) for r in rows]
    return SearchResponse(results=results, total=len(results))
