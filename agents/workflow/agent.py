"""Workflow agent: change-request impact.

Given a ChangeTicket the agent:
1. Searches the knowledge base for the target entity.
2. Gets downstream lineage (depth 3).
3. Gets OWNED_BY related entities.
4. Asks the LLM to draft an impact report, constrained to the retrieved evidence.
"""
from __future__ import annotations

import json

from adapters.llm.base import LLMProvider

from .grounding import ContextClient
from .models import (
    ChangeTicket,
    Citation,
    DownstreamAsset,
    ImpactReport,
    Owner,
)

_SYSTEM_PROMPT = """\
You are a change-impact analyst. You receive a change ticket and evidence retrieved from a \
knowledge base. Produce a concise JSON object with these keys:
  "suggested_approvers": list of owner names who should approve
  "suggested_tests": list of short test steps (max 5)
  "draft_comment": one paragraph for the change ticket

Rules:
- Only use the evidence provided. Do not invent asset names, owner names, or facts.
- If evidence is empty, set all lists to [] and draft_comment to "No downstream impact found in the knowledge base."
- Return valid JSON only, no prose outside it.
"""


def _make_user_message(ticket: ChangeTicket, assets: list[DownstreamAsset], owners: list[Owner]) -> str:
    asset_lines = "\n".join(
        f"  - {a.entity_type} '{a.entity_name}' (relation: {a.relation}, depth: {a.depth}, source: {a.citation.source_link})"
        for a in assets
    )
    owner_lines = "\n".join(
        f"  - {o.entity_name} (source: {o.citation.source_link})"
        for o in owners
    )
    return (
        f"Change ticket: {ticket.change_description}\n"
        f"Target: {ticket.entity_type} '{ticket.entity_name}'\n\n"
        f"Downstream assets ({len(assets)}):\n{asset_lines or '  (none)'}\n\n"
        f"Owners ({len(owners)}):\n{owner_lines or '  (none)'}\n"
    )


class WorkflowAgent:
    def __init__(self, context_client: ContextClient, llm: LLMProvider) -> None:
        self._ctx = context_client
        self._llm = llm

    def run(self, ticket: ChangeTicket) -> ImpactReport:
        # 1. Find the entity in the knowledge base.
        search_results = self._ctx.search_context(ticket.entity_name, limit=10)
        target_entity_id: str | None = None
        for r in search_results:
            if r.get("entity_name", "").lower() == ticket.entity_name.lower():
                target_entity_id = r.get("entity_id")
                break
        if target_entity_id is None and search_results:
            target_entity_id = search_results[0].get("entity_id")

        # 2. Downstream lineage.
        assets: list[DownstreamAsset] = []
        if target_entity_id:
            lineage = self._ctx.get_lineage(target_entity_id, direction="downstream", depth=3)
            nodes: list[dict] = lineage.get("nodes", [])
            edges: list[dict] = lineage.get("edges", [])
            edge_map: dict[str, str] = {}
            for e in edges:
                edge_map[e.get("dst_entity_id", "")] = e.get("relation", "READS_FROM")

            for node in nodes:
                nid = node.get("entity_id", "")
                if nid == target_entity_id:
                    continue
                source_link = node.get("source_link", "")
                harvested_at = node.get("harvested_at", "")
                sensitivity = node.get("sensitivity", "internal")
                assets.append(
                    DownstreamAsset(
                        entity_id=nid,
                        entity_name=node.get("entity_name", nid),
                        entity_type=node.get("entity_type", "Unknown"),
                        relation=edge_map.get(nid, "READS_FROM"),
                        depth=node.get("depth", 1),
                        citation=Citation(
                            source_link=source_link,
                            harvested_at=harvested_at,
                            sensitivity=sensitivity,
                        ),
                    )
                )

        # 3. Owners.
        owners: list[Owner] = []
        if target_entity_id:
            related = self._ctx.get_related(target_entity_id, relation="OWNED_BY")
            for r in related:
                owners.append(
                    Owner(
                        entity_id=r.get("entity_id", ""),
                        entity_name=r.get("entity_name", ""),
                        citation=Citation(
                            source_link=r.get("source_link", ""),
                            harvested_at=r.get("harvested_at", ""),
                            sensitivity=r.get("sensitivity", "internal"),
                        ),
                    )
                )

        # 4. LLM drafts the report.
        user_msg = _make_user_message(ticket, assets, owners)
        raw = self._llm.complete(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ]
        )
        try:
            llm_out = json.loads(raw)
        except Exception:
            llm_out = {}

        return ImpactReport(
            ticket=ticket,
            downstream_assets=assets,
            owners=owners,
            suggested_approvers=llm_out.get("suggested_approvers", [o.entity_name for o in owners]),
            suggested_tests=llm_out.get("suggested_tests", []),
            draft_comment=llm_out.get("draft_comment", ""),
        )
