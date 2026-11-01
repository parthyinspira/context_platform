"""Seeded in-memory demo graph and chunks for all four agent demo tasks."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DemoEntity:
    id: str
    type: str
    name: str
    source_url: str
    harvested_at: str
    sensitivity: str = "internal"
    props: dict = field(default_factory=dict)


@dataclass
class DemoEdge:
    src: str
    dst: str
    relation: str


@dataclass
class DemoChunk:
    id: str
    entity_id: str
    text: str
    source_url: str
    harvested_at: str
    sensitivity: str = "internal"


ENTITIES: list[DemoEntity] = [
    # --- Workflow agent demo data (change-request: rename CUSTOMER.CUST_ID) ---
    DemoEntity("tbl-customer", "Table", "CUSTOMER", "https://demo/db/customer", "2026-10-30T10:00:00Z"),
    DemoEntity("col-cust-id", "Column", "CUST_ID", "https://demo/db/customer/cust_id", "2026-10-30T10:00:00Z"),
    DemoEntity("job-etl-nightly", "Job", "etl_nightly_load", "https://demo/repo/etl/nightly_load.sql", "2026-10-30T10:00:00Z"),
    DemoEntity("tbl-revenue", "Table", "REVENUE_DAILY", "https://demo/db/revenue_daily", "2026-10-30T10:00:00Z"),
    DemoEntity("dash-revenue", "Dashboard", "Revenue Dashboard", "https://demo/bi/revenue-dashboard", "2026-10-30T10:00:00Z"),
    DemoEntity("person-data-eng", "Person", "Alice Eng", "https://demo/people/alice", "2026-10-30T10:00:00Z"),
    DemoEntity("team-data", "Team", "Data Engineering", "https://demo/teams/data-eng", "2026-10-30T10:00:00Z"),
    # --- Research agent demo data (how does customer data reach the revenue dashboard?) ---
    DemoEntity("svc-ingest", "Service", "CustomerIngestService", "https://demo/repo/ingest-svc", "2026-10-30T10:00:00Z"),
    DemoEntity("doc-arch", "Document", "Data Architecture Overview", "https://demo/docs/arch-overview.md", "2026-10-30T10:00:00Z"),
    # --- Prod support agent demo data (Revenue dashboard shows stale data) ---
    DemoEntity("job-broken-etl", "Job", "etl_weekly_transform", "https://demo/repo/etl/weekly_transform.sql", "2026-10-29T08:00:00Z"),
    DemoEntity("person-oncall", "Person", "Bob Ops", "https://demo/people/bob", "2026-10-30T10:00:00Z"),
    DemoEntity("doc-runbook", "Document", "Revenue Pipeline Runbook", "https://demo/docs/runbook.md", "2026-10-30T10:00:00Z"),
    # --- Call centre agent demo data (mid-year contribution change rule) ---
    DemoEntity("doc-policy-contrib", "Document", "HSA Contribution Policy 2026", "https://demo/docs/hsa-policy-2026.pdf", "2026-10-30T10:00:00Z", sensitivity="internal"),
    DemoEntity("doc-faq", "Document", "Member FAQ", "https://demo/docs/member-faq.md", "2026-10-30T10:00:00Z", sensitivity="internal"),
    DemoEntity("doc-restricted", "Document", "Internal Actuarial Report", "https://demo/docs/actuarial.pdf", "2026-10-30T10:00:00Z", sensitivity="restricted"),
]

EDGES: list[DemoEdge] = [
    DemoEdge("job-etl-nightly", "tbl-customer", "READS_FROM"),
    DemoEdge("job-etl-nightly", "tbl-revenue", "WRITES_TO"),
    # dash-revenue is derived FROM tbl-revenue
    DemoEdge("dash-revenue", "tbl-revenue", "DERIVED_FROM"),
    DemoEdge("col-cust-id", "tbl-customer", "CONTAINS"),
    DemoEdge("tbl-customer", "team-data", "OWNED_BY"),
    DemoEdge("tbl-customer", "person-data-eng", "OWNED_BY"),
    DemoEdge("svc-ingest", "tbl-customer", "WRITES_TO"),
    DemoEdge("job-broken-etl", "tbl-revenue", "WRITES_TO"),
    DemoEdge("job-broken-etl", "tbl-customer", "READS_FROM"),
    DemoEdge("tbl-revenue", "person-oncall", "OWNED_BY"),
]

CHUNKS: list[DemoChunk] = [
    DemoChunk(
        "chunk-arch-1", "doc-arch",
        "Customer data is ingested by CustomerIngestService, which writes to the CUSTOMER table. "
        "The nightly ETL job reads CUSTOMER and writes to REVENUE_DAILY. "
        "The Revenue Dashboard reads REVENUE_DAILY via a BI connector.",
        "https://demo/docs/arch-overview.md", "2026-10-30T10:00:00Z",
    ),
    DemoChunk(
        "chunk-runbook-1", "doc-runbook",
        "If the Revenue Dashboard shows stale data, first check etl_weekly_transform status. "
        "Page the on-call engineer (Bob Ops) if the job has not run in 24 hours. "
        "Runbook step 3: verify REVENUE_DAILY last_updated timestamp.",
        "https://demo/docs/runbook.md", "2026-10-30T10:00:00Z",
    ),
    DemoChunk(
        "chunk-policy-1", "doc-policy-contrib",
        "Members may change their HSA contribution amount once per plan year at open enrollment "
        "or upon a qualifying mid-year life event (marriage, divorce, birth, adoption, loss of "
        "other coverage). The change takes effect the first of the following month. "
        "Effective date: 2026-01-01.",
        "https://demo/docs/hsa-policy-2026.pdf", "2026-10-30T10:00:00Z",
    ),
    DemoChunk(
        "chunk-faq-1", "doc-faq",
        "Q: Can I change my contribution mid-year?\n"
        "A: Yes, if you have a qualifying life event. Contact your HR administrator to submit "
        "a mid-year change form within 30 days of the event.",
        "https://demo/docs/member-faq.md", "2026-10-30T10:00:00Z",
    ),
]


def entity_by_id(entity_id: str) -> Optional[DemoEntity]:
    return next((e for e in ENTITIES if e.id == entity_id), None)


def entities_by_type(entity_type: str) -> list[DemoEntity]:
    return [e for e in ENTITIES if e.type == entity_type]


def downstream_of(entity_id: str, depth: int = 3) -> list[str]:
    """Return entity IDs downstream from entity_id.

    Follows: things that READS_FROM entity_id, things entity_id WRITES_TO,
    and things that are DERIVED_FROM entity_id.
    """
    visited: set[str] = set()
    frontier = [entity_id]
    for _ in range(depth):
        next_frontier = []
        for node in frontier:
            for edge in EDGES:
                # Something reads from this node (it is downstream)
                if edge.dst == node and edge.relation == "READS_FROM":
                    if edge.src not in visited:
                        visited.add(edge.src)
                        next_frontier.append(edge.src)
                # This node writes to something
                if edge.src == node and edge.relation == "WRITES_TO":
                    if edge.dst not in visited:
                        visited.add(edge.dst)
                        next_frontier.append(edge.dst)
                # Something is derived from this node
                if edge.dst == node and edge.relation == "DERIVED_FROM":
                    if edge.src not in visited:
                        visited.add(edge.src)
                        next_frontier.append(edge.src)
        frontier = next_frontier
    return list(visited)


def upstream_of(entity_id: str, depth: int = 3) -> list[str]:
    """Return entity IDs upstream of entity_id (things that feed it).

    Follows: things entity_id READS_FROM, things that WRITE_TO entity_id,
    and things entity_id is DERIVED_FROM.
    """
    visited: set[str] = set()
    frontier = [entity_id]
    for _ in range(depth):
        next_frontier = []
        for node in frontier:
            for edge in EDGES:
                # This node reads from something (that something is upstream)
                if edge.src == node and edge.relation == "READS_FROM":
                    if edge.dst not in visited:
                        visited.add(edge.dst)
                        next_frontier.append(edge.dst)
                # Something writes to this node (that something is upstream)
                if edge.dst == node and edge.relation == "WRITES_TO":
                    if edge.src not in visited:
                        visited.add(edge.src)
                        next_frontier.append(edge.src)
                # This node is derived from something (that something is upstream)
                if edge.src == node and edge.relation == "DERIVED_FROM":
                    if edge.dst not in visited:
                        visited.add(edge.dst)
                        next_frontier.append(edge.dst)
        frontier = next_frontier
    return list(visited)


def owners_of(entity_id: str) -> list[str]:
    return [e.dst for e in EDGES if e.src == entity_id and e.relation == "OWNED_BY"]


def search_chunks(query_terms: list[str], max_sensitivity: str = "internal") -> list[DemoChunk]:
    allowed = {"public", "internal"} if max_sensitivity == "internal" else {"public", "internal", "restricted"}
    results = []
    for chunk in CHUNKS:
        if chunk.sensitivity not in allowed:
            continue
        text_lower = chunk.text.lower()
        if any(term.lower() in text_lower for term in query_terms):
            results.append(chunk)
    return results
