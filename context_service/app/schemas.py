from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SearchResult(BaseModel):
    entity_id: str
    entity_type: str
    entity_name: str
    chunk_id: str
    text: str
    score: float
    source_link: str
    harvested_at: str
    sensitivity: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


class LineageNode(BaseModel):
    entity_id: str
    entity_type: str
    entity_name: str
    depth: int


class LineageEdge(BaseModel):
    src_entity_id: str
    dst_entity_id: str
    relation: str
    confidence: float | None


class LineageResponse(BaseModel):
    root_entity_id: str
    direction: str
    nodes: list[LineageNode]
    edges: list[LineageEdge]


class RelatedResult(BaseModel):
    entity_id: str
    entity_type: str
    entity_name: str
    relation: str
    direction: str


class EntityResult(BaseModel):
    entity_id: str
    entity_type: str
    entity_name: str
    props: dict[str, Any]
    source_link: str
    sensitivity: str
    harvested_at: str | None
    related: list[RelatedResult]
