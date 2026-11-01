# KAN-100: Agent demo script and rehearsal (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-100
Branch: kepler/kan-100-agent-demo-script-rehearsal

## Scope
In:
- `agents/` Python package: shared `grounding.py` + four agent modules (workflow, research, prod_support, call_centre)
- Deterministic mock grounding so the demo is repeatable without a live backend
- `agents/demo_data.py`: seeded in-memory graph + chunks for all four demo tasks
- `AgentsScreen.jsx`: agent picker, task display, step trace, citations, with/without-KB toggle
- Graph trace overlay in `GraphCanvas`: agent-retrieved nodes pulse and show retrieval-order badge
- `api.js`: `runAgentDemo(agentName, taskKey)` → returns steps + retrieved_node_ids + answer
- `docs/DEMO_SCRIPT.md`: step-by-step rehearsal script for all four agents
- Unit tests: one per agent confirming retrieved node IDs and citation coverage

Out:
- Real LLM calls (mock returns deterministic answers)
- New Postgres migrations (agents use existing entities/edges via context service)
- New API service endpoints (UI calls a thin in-process mock endpoint via a Vite proxy stub)
- Evaluation harness / CI eval runs (separate story)

## Acceptance criteria (from Jira)
1. Scripted demo of all four agents (workflow, research, prod support, call centre).
2. Graph trace overlay showing retrieved nodes pulsing and numbered in retrieval order.

## Requirements
- R1: Each agent module exposes `run(task_key) -> AgentResult` (steps, retrieved_node_ids, answer, citations). Given deterministic demo data, the same task_key always produces the same result.
- R2: `grounding.py` implements the shared pattern: search → expand → freshness → compose with citations → escalate if no evidence.
- R3: `GraphCanvas` accepts an optional `agentTrace` prop (list of node IDs in order); matching nodes gain the `.agent-retrieved` class (pulse animation, numbered badge).
- R4: `AgentsScreen` lets the user pick an agent and a pre-set task, runs the demo, streams steps, and shows citations that highlight the node on the graph.
- R5: `docs/DEMO_SCRIPT.md` provides a cue-by-cue script covering all four agents and the graph overlay.

## Tasks
- [x] 1. Write `agents/` package: grounding.py + four agents + demo_data.py (test first)
- [x] 2. Add graph trace overlay to `GraphCanvas` (agentTrace prop)
- [x] 3. Build `AgentsScreen.jsx` with step trace, citations, KB toggle
- [x] 4. Wire Agents nav in App.jsx + add `runAgentDemo` to api.js
- [x] 5. Write `docs/DEMO_SCRIPT.md`
- [x] 6. Verify: secret-scan, spec_check, unit tests pass

## Risks / not verifiable here
- Real LLM / MCP backend integration not tested (agents use mock grounding); a separate story covers live eval.
- Graph overlay animation requires a browser; tested structurally (class application) only in unit tests.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
