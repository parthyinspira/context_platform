# Demo agents capability

Added in KAN-100.

## What was built
- `agents/demo_grounding.py`: mock grounding helpers (search_entities, expand_downstream, expand_upstream, get_owners, search_docs, check_freshness, ordered_node_ids) using seeded demo data — no DB or LLM required
- `agents/demo_data.py`: seeded in-memory graph (14 entities, 10 edges, 4 chunks) for all four demo tasks
- `agents/workflow/demo_agent.py`: workflow demo agent (rename CUSTOMER.CUST_ID → retrieves downstream assets and owners)
- `agents/research/agent.py`: research demo agent (customer data → revenue dashboard, flags false claims as UNVERIFIED)
- `agents/prod_support/agent.py`: prod-support demo agent (stale data triage, surfaces broken upstream job)
- `agents/call_centre/agent.py`: call-centre demo agent (policy answers with citation; escalates out-of-scope)
- `POST /agents/{name}/run` API endpoint (`api/app/routes_agents.py`)
- `ui/src/components/AgentsScreen.jsx`: agent picker, task selector, step trace, citations, with/without-KB toggle
- Graph trace overlay in `GraphCanvas`: `agentTrace` prop — retrieved nodes get amber border + retrieval-order badge
- `docs/DEMO_SCRIPT.md`: cue-by-cue rehearsal script for all four agents

## Acceptance criteria (verified)
1. Scripted demo of all four agents — 17 unit tests pass; each agent produces deterministic results with citations.
2. Graph trace overlay — `agentTrace` prop applies `.agent-retrieved` class with amber double-border and numbered badge.

## Not in scope here
Real LLM / MCP backend integration and evaluation harness (separate stories).
