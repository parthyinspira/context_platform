"""Request/response models for the lineage traversal endpoint (KAN-48)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LineageNodeOut(BaseModel):
    id: str
    type: str
    name: str
    source_id: str
    props: dict[str, Any] = {}
    depth: int
    source_link: str | None = None
    harvested_at: str | None = None
    sensitivity: str | None = None


class LineageEdgeOut(BaseModel):
    id: str
    src_entity_id: str
    dst_entity_id: str
    relation: str
    confidence: float


class LineageOut(BaseModel):
    start_entity_id: str
    direction: str
    depth: int
    nodes: list[LineageNodeOut] = []
    edges: list[LineageEdgeOut] = []
