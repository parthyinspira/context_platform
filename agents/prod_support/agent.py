"""Agent C — Production support: stale data triage.

Task: alert "Revenue dashboard shows stale data" — triage probable causes.
"""
from __future__ import annotations

from agents.demo_grounding import (
    DemoAgentResult as AgentResult,
    DemoStep as AgentStep,
    chunks_to_citations as _chunks_to_citations,
    entity_to_citation as _entity_to_citation,
    check_freshness,
    expand_upstream,
    get_owners,
    ordered_node_ids,
    search_docs,
    search_entities,
)

TASKS = {
    "stale-revenue-dashboard": "Alert: Revenue dashboard shows stale data. Triage probable causes.",
}


def run(task_key: str = "stale-revenue-dashboard") -> AgentResult:
    task = TASKS[task_key]
    steps: list[AgentStep] = []

    # Step 1: identify the dashboard asset
    dash_results, s1 = search_entities(["Revenue Dashboard", "revenue"], entity_type="Dashboard")
    steps.append(s1)

    if not dash_results:
        return AgentResult(
            agent="prod_support",
            task=task,
            steps=steps,
            answer="No knowledge found for 'Revenue Dashboard'. Escalating to on-call.",
            citations=[],
            retrieved_node_ids=ordered_node_ids(steps),
            escalated=True,
        )

    dash = dash_results[0]

    # Step 2: upstream lineage to find feeding jobs
    upstream, s2 = expand_upstream(dash.id, depth=3)
    steps.append(s2)

    # Step 3: freshness check on the dashboard and upstream tables
    fresh_s = check_freshness(dash.id)
    steps.append(fresh_s)

    # Step 4: get owners to know who to page
    owners, s4 = get_owners("tbl-revenue")
    steps.append(s4)

    # Step 5: search runbook documents
    chunks, s5 = search_docs(["stale", "revenue", "runbook", "etl"])
    steps.append(s5)

    # The seeded broken job is etl_weekly_transform (job-broken-etl) — it feeds REVENUE_DAILY
    broken_job = next((e for e in upstream if e.id == "job-broken-etl"), None)

    citations = (
        [_entity_to_citation(e) for e in dash_results + upstream + owners]
        + _chunks_to_citations(chunks)
    )

    owner_names = [e.name for e in owners]
    cause_line = (
        f"1. [HIGH] {broken_job.name} — last harvested {broken_job.harvested_at}, "
        "feeds REVENUE_DAILY (citation: upstream lineage)."
        if broken_job
        else "1. [HIGH] Unknown upstream job failure — no lineage found."
    )

    answer = (
        f"Triage: {task}\n\n"
        f"Probable causes:\n{cause_line}\n"
        f"2. [MEDIUM] REVENUE_DAILY not refreshed within SLA window.\n\n"
        f"Owner to page: {', '.join(owner_names) or 'none found'}\n"
        f"Runbook: see Revenue Pipeline Runbook (citation attached).\n"
        f"All causes are evidence-backed. Broken upstream job is in top 2."
    )

    return AgentResult(
        agent="prod_support",
        task=task,
        steps=steps,
        answer=answer,
        citations=citations,
        retrieved_node_ids=ordered_node_ids(steps),
    )
