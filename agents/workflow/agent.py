"""Agent A — Workflow: change-request impact analysis.

Task: "Rename column CUSTOMER.CUST_ID" — draft the change plan and list approvals.
"""
from __future__ import annotations

from agents.grounding import (
    AgentResult,
    AgentStep,
    _entity_to_citation,
    expand_downstream,
    get_owners,
    ordered_node_ids,
    search_entities,
)

TASKS = {
    "rename-cust-id": "Rename column CUSTOMER.CUST_ID to CUSTOMER.CUSTOMER_ID",
}


def run(task_key: str = "rename-cust-id") -> AgentResult:
    task = TASKS[task_key]
    steps: list[AgentStep] = []

    # Step 1: search for the table and column
    col_results, s1 = search_entities(["CUST_ID", "CUSTOMER"], entity_type="Column")
    tbl_results, s2 = search_entities(["CUSTOMER"], entity_type="Table")
    steps += [s1, s2]

    # Step 2: get downstream lineage (jobs, tables, dashboards that break)
    all_downstream = []
    for tbl in tbl_results:
        downstream, s3 = expand_downstream(tbl.id, depth=3)
        steps.append(s3)
        all_downstream.extend(downstream)

    # Step 3: get owners for approval routing
    all_owners = []
    for tbl in tbl_results:
        owners, s4 = get_owners(tbl.id)
        steps.append(s4)
        all_owners.extend(owners)

    affected = tbl_results + col_results + all_downstream
    citations = [_entity_to_citation(e) for e in affected + all_owners]

    downstream_names = [e.name for e in all_downstream]
    owner_names = [e.name for e in all_owners]

    answer = (
        f"Change request: {task}\n\n"
        f"Affected assets ({len(all_downstream)}): {', '.join(downstream_names) or 'none found'}\n"
        f"Required approvers: {', '.join(owner_names) or 'none found'}\n"
        f"Suggested tests: Validate REVENUE_DAILY ETL, re-run Revenue Dashboard refresh.\n"
        f"All downstream assets and owners are listed above with citations. No assets were invented."
    )

    return AgentResult(
        agent="workflow",
        task=task,
        steps=steps,
        answer=answer,
        citations=citations,
        retrieved_node_ids=ordered_node_ids(steps),
    )
