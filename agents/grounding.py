"""Shared grounding pattern for all demo agents.

Each agent calls these helpers; the mock implementation uses demo_data
so the demo is repeatable without a live backend.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from agents.demo_data import (
    DemoChunk,
    DemoEntity,
    downstream_of,
    entities_by_type,
    entity_by_id,
    owners_of,
    search_chunks,
    upstream_of,
)


@dataclass
class Citation:
    entity_id: str
    entity_name: str
    source_url: str
    harvested_at: str
    sensitivity: str


@dataclass
class AgentStep:
    kind: str          # "search" | "expand" | "freshness" | "answer" | "escalate"
    description: str
    retrieved_ids: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    agent: str
    task: str
    steps: list[AgentStep]
    answer: str
    citations: list[Citation]
    retrieved_node_ids: list[str]   # ordered — matches graph overlay numbering
    escalated: bool = False


def _entity_to_citation(entity: DemoEntity) -> Citation:
    return Citation(
        entity_id=entity.id,
        entity_name=entity.name,
        source_url=entity.source_url,
        harvested_at=entity.harvested_at,
        sensitivity=entity.sensitivity,
    )


def _chunks_to_citations(chunks: list[DemoChunk]) -> list[Citation]:
    seen: set[str] = set()
    result = []
    for c in chunks:
        if c.entity_id not in seen:
            seen.add(c.entity_id)
            e = entity_by_id(c.entity_id)
            if e:
                result.append(Citation(
                    entity_id=e.id,
                    entity_name=e.name,
                    source_url=c.source_url,
                    harvested_at=c.harvested_at,
                    sensitivity=c.sensitivity,
                ))
    return result


def search_entities(query_terms: list[str], entity_type: Optional[str] = None) -> tuple[list[DemoEntity], AgentStep]:
    """Step 1 — search the knowledge base."""
    if entity_type:
        results = [e for e in entities_by_type(entity_type) if any(t.lower() in e.name.lower() for t in query_terms)]
    else:
        all_entities = []
        from agents import demo_data
        for e in demo_data.ENTITIES:
            if any(t.lower() in e.name.lower() for t in query_terms):
                all_entities.append(e)
        results = all_entities
    step = AgentStep(
        kind="search",
        description=f"search_context({query_terms!r}) → {len(results)} entities",
        retrieved_ids=[e.id for e in results],
    )
    return results, step


def expand_downstream(entity_id: str, depth: int = 3) -> tuple[list[DemoEntity], AgentStep]:
    ids = downstream_of(entity_id, depth)
    entities = [e for eid in ids if (e := entity_by_id(eid))]
    step = AgentStep(
        kind="expand",
        description=f"get_lineage(downstream, depth={depth}, from={entity_id}) → {len(entities)} nodes",
        retrieved_ids=ids,
    )
    return entities, step


def expand_upstream(entity_id: str, depth: int = 3) -> tuple[list[DemoEntity], AgentStep]:
    ids = upstream_of(entity_id, depth)
    entities = [e for eid in ids if (e := entity_by_id(eid))]
    step = AgentStep(
        kind="expand",
        description=f"get_lineage(upstream, depth={depth}, from={entity_id}) → {len(entities)} nodes",
        retrieved_ids=ids,
    )
    return entities, step


def get_owners(entity_id: str) -> tuple[list[DemoEntity], AgentStep]:
    ids = owners_of(entity_id)
    entities = [e for eid in ids if (e := entity_by_id(eid))]
    step = AgentStep(
        kind="expand",
        description=f"get_related(OWNED_BY, {entity_id}) → {len(entities)} owners",
        retrieved_ids=ids,
    )
    return entities, step


def search_docs(query_terms: list[str], max_sensitivity: str = "internal") -> tuple[list[DemoChunk], AgentStep]:
    chunks = search_chunks(query_terms, max_sensitivity)
    step = AgentStep(
        kind="search",
        description=f"search_context(docs, {query_terms!r}, sensitivity<={max_sensitivity}) → {len(chunks)} passages",
        retrieved_ids=[c.entity_id for c in chunks],
    )
    return chunks, step


def check_freshness(entity_id: str) -> AgentStep:
    e = entity_by_id(entity_id)
    ts = e.harvested_at if e else "unknown"
    return AgentStep(
        kind="freshness",
        description=f"get_source_status({entity_id}) → last harvested {ts}",
        retrieved_ids=[entity_id] if e else [],
    )


def ordered_node_ids(steps: list[AgentStep]) -> list[str]:
    """Deduplicated retrieval order for the graph overlay."""
    seen: set[str] = set()
    result = []
    for step in steps:
        for nid in step.retrieved_ids:
            if nid not in seen:
                seen.add(nid)
                result.append(nid)
    return result
