# KAN-32: MCP tool search_context (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-32   Branch: kepler/kan-32-mcp-tool-search-context

## Scope
In: `search_context` MCP tool — text search over chunks, returning source_link, harvested_at, sensitivity; tombstoned entities excluded; sensitivity passed through in results.
Out: get_entity, get_related, get_lineage tools (separate stories); caller-based ACL (separate story); vector/hybrid search (enhancement).

## Acceptance criteria (from Jira)
1. `search_context` returns top results with source link, `harvested_at` and `sensitivity`.

## Requirements (only new or changed behaviour; at most 5)
- The system SHALL expose an MCP tool `search_context(query, limit=5)` that searches chunk text and returns up to `limit` results, each with `text`, `source_link`, `harvested_at`, `sensitivity`. (scenario: Given indexed chunks with a source, When `search_context("keyword")` is called, Then results contain source_link, harvested_at and sensitivity.)
- The system SHALL exclude chunks whose linked entity has `tombstoned_at IS NOT NULL`. (scenario: Given a tombstoned entity, When search_context is called, Then its chunks are not returned.)

## Tasks
- [x] 1. Create mcp/ package with search.py (DB query logic) and server.py (FastMCP tool registration) (test first)
- [x] 2. Write tests in mcp/tests/test_search_context.py using in-memory fakes
- [x] 3. Add mcp service to docker-compose.yml
- [x] 4. Update pyproject.toml ruff include

## Risks / not verifiable here
- Vector/embedding search not verified (no embeddings in test fixtures); text ILIKE search is used.
- Docker compose runtime not verified (no Docker run per lite mode rules).

## Approval
Approved by: auto (user started spec-auto), 2026-10-31
