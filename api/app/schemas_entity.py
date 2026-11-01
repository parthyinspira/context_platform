"""Request/response models for the entity detail endpoint (KAN-68)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EdgeNeighborOut(BaseModel):
    id: str
    direction: str  # "out" | "in"
    entity_id: str
    entity_type: str
    entity_name: str


class CitationOut(BaseModel):
    source_link: str
    harvested_at: str
    run_id: str | None = None


class EntityOut(BaseModel):
    id: str
    type: str
    name: str
    props: dict[str, Any] = {}
    owner: str
    source_uri: str
    edges_by_relation: dict[str, list[EdgeNeighborOut]] = {}
    citations: list[CitationOut] = []
