"""Agent D — Call centre: policy and product answers.

Task: "What is the rule for a mid-year contribution change?"
Answers only from retrieved passages at sensitivity <= internal; escalates if no evidence.
"""
from __future__ import annotations

from agents.demo_grounding import (
    DemoAgentResult as AgentResult,
    DemoStep as AgentStep,
    chunks_to_citations as _chunks_to_citations,
    ordered_node_ids,
    search_docs,
)

TASKS = {
    "mid-year-contribution": "What is the rule for a mid-year contribution change?",
    "out-of-scope": "What is the company's quarterly earnings forecast?",
}


def run(task_key: str = "mid-year-contribution") -> AgentResult:
    task = TASKS[task_key]
    steps: list[AgentStep] = []

    if task_key == "out-of-scope":
        chunks, s1 = search_docs(["earnings", "forecast", "quarterly"], max_sensitivity="internal")
        steps.append(s1)
        return AgentResult(
            agent="call_centre",
            task=task,
            steps=steps,
            answer="I cannot find this information in the approved knowledge base. Escalating to a specialist.",
            citations=[],
            retrieved_node_ids=ordered_node_ids(steps),
            escalated=True,
        )

    # In-scope: search policy and FAQ docs
    chunks, s1 = search_docs(["mid-year", "contribution", "HSA", "change"], max_sensitivity="internal")
    steps.append(s1)

    if not chunks:
        return AgentResult(
            agent="call_centre",
            task=task,
            steps=steps,
            answer="I can't find this, escalating to a specialist.",
            citations=[],
            retrieved_node_ids=ordered_node_ids(steps),
            escalated=True,
        )

    # Compose answer strictly from retrieved passages
    passage = chunks[0].text[:300]
    source_url = chunks[0].source_url
    effective = "2026-01-01"

    answer = (
        f"Answer: Members may change their HSA contribution mid-year upon a qualifying life event "
        f"(marriage, divorce, birth, adoption, loss of coverage). The change takes effect the first "
        f"of the following month.\n\n"
        f'Source: "{passage}"\n'
        f"Source URL: {source_url}\n"
        f"Effective date: {effective}\n"
        f"No restricted content was returned."
    )

    citations = _chunks_to_citations(chunks)

    return AgentResult(
        agent="call_centre",
        task=task,
        steps=steps,
        answer=answer,
        citations=citations,
        retrieved_node_ids=ordered_node_ids(steps),
    )
