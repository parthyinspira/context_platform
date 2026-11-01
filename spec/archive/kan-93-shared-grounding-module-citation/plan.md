# KAN-93: Shared grounding module with citation contract (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-93   Branch: kepler/kan-93-shared-grounding-module-citation

## Scope
In: agents/grounding.py — search, expand (lineage/related), freshness check, cited answer, refuse/escalate; claims separated from evidence.
Out: Demo agent loops, MCP server changes, UI, new DB migrations.

## Acceptance criteria (from Jira)
1. grounding.py implements search, expand, freshness check, cited answer, refuse/escalate.
2. Claims separated from evidence in the output.

## Requirements (only new or changed behaviour)
- The system SHALL provide a `ground(query, conn, llm, *, sensitivity_filter, freshness_threshold_hours)` function that: searches for relevant chunks, expands via lineage, checks freshness, composes a cited answer, and refuses/escalates when no evidence is found. (Scenario: Given a query with matching chunks, When ground() is called, Then it returns a GroundedAnswer with claims each referencing a Citation, none invented.)
- The system SHALL separate claims from evidence: GroundedAnswer.claims is a list of Claim(text, citations); GroundedAnswer.evidence is the raw retrieved chunks. Claims without citations are flagged unverified or dropped.
- The system SHALL check freshness: chunks whose harvested_at is older than freshness_threshold_hours carry Citation.stale=True.
- The system SHALL refuse when evidence list is empty: return GroundedAnswer with claims=[], refused=True, refused_reason="no_evidence".

## Tasks
- [x] 1. Write tests first: tests/agents/test_grounding.py (search, expand, freshness, refuse/escalate scenarios)
- [x] 2. Implement agents/grounding.py with GroundedAnswer, Claim, Citation dataclasses and ground() function
- [x] 3. Create agents/__init__.py (empty)
- [x] 4. Create tests/agents/__init__.py (empty)
- [x] 5. Run spec_check and secret_scan

## Risks / not verifiable here
- LLM-dependent claim extraction tested with a stub; live LLM output format may vary.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
