# KAN-94: Workflow agent: change-request impact (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-94   Branch: kepler/kan-94-workflow-agent-change-request

## Scope
In: `agents/workflow/` — agent that accepts a change ticket, grounds via the context service HTTP API (search_context, get_lineage, get_related), and returns a structured impact report.  
In: Golden tasks tests (pytest, mocked context client) proving all known downstream assets and owners appear, none invented.  
Out: Docker service wiring, UI screen, real database, new API endpoints.

## Acceptance criteria (from Jira)
1. Given a change ticket, outputs impact report with downstream assets, owners, approvals.
2. Passes golden tasks: all known downstream assets and owners are listed, none invented.

## Requirements
- REQ-1: The agent SHALL accept a ChangeTicket (entity_name, entity_type, change_description) and return an ImpactReport (downstream_assets, owners, suggested_approvers, suggested_tests, draft_comment, citations). (Given a valid change ticket / When run / Then ImpactReport has all fields populated from retrieved context)
- REQ-2: The agent SHALL call search_context for the named entity, get_lineage(downstream, depth=3) for downstream assets, and get_related(OWNED_BY) for owners; all claims in the report SHALL have a citation. (Given mocked context responses / When run / Then every asset and owner in the report maps to a retrieved result)
- REQ-3: The agent SHALL NOT invent assets or owners absent from the retrieved context; if no evidence is found for a claim it is omitted or flagged "unverified". (Given context returns empty / When run / Then report lists no downstream assets or owners)

## Tasks
- [x] 1. Write tests first: `agents/workflow/tests/test_agent.py` with golden tasks (mocked ContextClient)
- [x] 2. Implement `agents/workflow/models.py` (ChangeTicket, ImpactReport, Citation)
- [x] 3. Implement `agents/workflow/grounding.py` (ContextClient wrapping context service HTTP API)
- [x] 4. Implement `agents/workflow/agent.py` (WorkflowAgent.run → ImpactReport)

## Risks / not verifiable here
- LLM quality of the draft comment: tested with a deterministic stub that returns a canned completion; real quality needs a live LLM run.
- Real DB lineage chains: golden tasks use mocked HTTP responses seeded from DEMO_AGENTS.md scenario (SQL repo → job → dashboard).

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
