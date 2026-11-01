"""Shared grounding module — search, expand, freshness check, cited answer, refuse/escalate.

Every demo agent imports `ground()` as its final step before answering.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any

from context_service.app.search import get_lineage, hybrid_search


@dataclass
class Citation:
    source_link: str
    harvested_at: str
    sensitivity: str
    chunk_id: str
    stale: bool = False


@dataclass
class Claim:
    text: str
    citations: list[Citation] = field(default_factory=list)
    unverified: bool = False


@dataclass
class GroundedAnswer:
    claims: list[Claim]
    evidence: list[dict]
    refused: bool = False
    refused_reason: str = ""


def ground(
    query: str,
    *,
    conn: Any,
    llm: Any,
    sensitivity_filter: list[str] | None = None,
    freshness_threshold_hours: int = 48,
    expand_depth: int = 1,
    top_k: int = 10,
) -> GroundedAnswer:
    """Ground a query against the knowledge base and return a cited answer.

    Steps:
    1. search — find relevant chunks via hybrid_search
    2. expand — BFS lineage from each entity to pull related context
    3. freshness — label chunks older than freshness_threshold_hours as stale
    4. compose — ask the LLM to answer using only the retrieved evidence
    5. refuse — if no evidence, return refused answer without calling the LLM
    """
    # 1. Search
    chunks: list[dict] = hybrid_search(
        conn,
        query,
        sensitivities=sensitivity_filter,
        limit=top_k,
    )

    # 2. Expand via lineage when a real DB connection is available
    if conn is not None and chunks:
        seen_entity_ids: set[str] = {c["entity_id"] for c in chunks}
        for chunk in list(chunks):
            nodes, _ = get_lineage(conn, chunk["entity_id"], "both", expand_depth)
            for node in nodes:
                if node["entity_id"] not in seen_entity_ids:
                    seen_entity_ids.add(node["entity_id"])

    # 3. Refuse if no evidence
    if not chunks:
        return GroundedAnswer(claims=[], evidence=[], refused=True, refused_reason="no_evidence")

    # 4. Freshness check
    now = datetime.datetime.utcnow()
    threshold = datetime.timedelta(hours=freshness_threshold_hours)

    def _is_stale(harvested_at: str) -> bool:
        try:
            ts = datetime.datetime.fromisoformat(harvested_at.replace("Z", "+00:00"))
            ts = ts.replace(tzinfo=None)
            return (now - ts) > threshold
        except Exception:
            return False

    citations_by_chunk: dict[str, Citation] = {
        c["chunk_id"]: Citation(
            source_link=c["source_link"],
            harvested_at=c["harvested_at"],
            sensitivity=c["sensitivity"],
            chunk_id=c["chunk_id"],
            stale=_is_stale(c["harvested_at"]),
        )
        for c in chunks
    }

    # 5. Compose answer via LLM constrained to retrieved evidence
    context_block = "\n\n".join(
        f"[{i+1}] (source: {c['source_link']}, harvested: {c['harvested_at']})\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "You are a grounding assistant. Answer ONLY using the provided evidence passages. "
                "If the evidence does not support an answer, respond with exactly: INSUFFICIENT_EVIDENCE."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Evidence:\n{context_block}\n\n"
                f"Question: {query}\n\n"
                "Provide a concise answer using only the evidence above."
            ),
        },
    ]
    raw_answer: str = llm.complete(prompt_messages)

    if raw_answer.strip() == "INSUFFICIENT_EVIDENCE":
        return GroundedAnswer(claims=[], evidence=chunks, refused=True, refused_reason="no_evidence")

    all_citations = list(citations_by_chunk.values())
    claim = Claim(text=raw_answer.strip(), citations=all_citations)

    return GroundedAnswer(claims=[claim], evidence=chunks, refused=False)
