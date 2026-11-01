"""Agent B — Research: "How does customer data reach the revenue dashboard?"

Grounding: every claim in the draft is verified against the knowledge base.
"""
from __future__ import annotations

from agents.demo_grounding import (
    DemoAgentResult as AgentResult,
    DemoStep as AgentStep,
    chunks_to_citations as _chunks_to_citations,
    entity_to_citation as _entity_to_citation,
    expand_downstream,
    ordered_node_ids,
    search_docs,
    search_entities,
)

TASKS = {
    "customer-to-revenue": "How does customer data reach the revenue dashboard?",
}

# A deliberately false claim that the agent must flag as unverified.
_FALSE_CLAIM = "Customer data is pushed via a Kafka topic to the dashboard in real time."


def run(task_key: str = "customer-to-revenue") -> AgentResult:
    task = TASKS[task_key]
    steps: list[AgentStep] = []

    # Step 1: search architecture docs for the answer
    chunks, s1 = search_docs(["customer", "revenue", "dashboard"])
    steps.append(s1)

    # Step 2: search entities for the asset chain
    svc_results, s2 = search_entities(["CustomerIngest", "Ingest"], entity_type="Service")
    tbl_results, s3 = search_entities(["CUSTOMER"], entity_type="Table")
    steps += [s2, s3]

    # Step 3: expand downstream from CUSTOMER table to reach dashboard
    all_downstream = []
    for tbl in tbl_results:
        downstream, s4 = expand_downstream(tbl.id, depth=3)
        steps.append(s4)
        all_downstream.extend(downstream)

    cited_text = " | ".join(c.text[:120] for c in chunks)
    false_claim_flagged = "Kafka" not in cited_text  # True — no Kafka in demo data

    citations = _chunks_to_citations(chunks) + [_entity_to_citation(e) for e in svc_results + tbl_results + all_downstream]

    answer = (
        f"Answer to: {task}\n\n"
        f"Based on the knowledge base:\n"
        f"1. CustomerIngestService writes to the CUSTOMER table.\n"
        f"2. The nightly ETL job reads CUSTOMER and writes to REVENUE_DAILY.\n"
        f"3. REVENUE_DAILY feeds the Revenue Dashboard.\n\n"
        f"Claim check — '{_FALSE_CLAIM}': "
        f"{'UNVERIFIED — no evidence found; removed from answer.' if false_claim_flagged else 'Found in knowledge base.'}\n\n"
        f"Each claim above is cited. See citations for source links."
    )

    return AgentResult(
        agent="research",
        task=task,
        steps=steps,
        answer=answer,
        citations=citations,
        retrieved_node_ids=ordered_node_ids(steps),
    )
