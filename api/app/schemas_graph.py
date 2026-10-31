"""Request/response models for the graph query endpoint (KAN-58)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class GraphNodeOut(BaseModel):
    id: str
    type: str
    name: str
    source_id: str
    props: dict[str, Any] = {}


class GraphEdgeOut(BaseModel):
    id: str
    src_entity_id: str
    dst_entity_id: str
    relation: str
    confidence: float
    source_id: str


class GraphOut(BaseModel):
    nodes: list[GraphNodeOut] = []
    edges: list[GraphEdgeOut] = []
