## Story
KAN-33 — MCP tool `get_related(entity)`

## What was built
- `mcp_server/tools/get_related.py`: depth-limited edge traversal via a `WITH RECURSIVE` CTE. Accepts `entity_id`, optional `relation` filter, `depth` (1–10, default 3), `direction` (out/in/both). Excludes tombstoned entities at the DB level.
- `mcp_server/server.py`: MCP JSON-RPC server (FastAPI, streamable HTTP on port 8002). Handles `initialize`, `tools/list`, `tools/call` for `get_related`.
- `mcp_server/db.py`, `Dockerfile`, `requirements.txt`: service scaffold following the existing api/ pattern.
- `docker-compose.yml`: added `mcp_server` service depending on postgres + migrate.
- `spec/capabilities/mcp-retrieval.md`: added `get_related` requirement + two-hop scenario.
- 9 unit tests (fake DB, no live Postgres), all passing.

## Evidence per AC
| AC | Evidence |
|---|---|
| traverses edges depth-limited via recursive CTE | `_CTE_SQL` in `get_related.py`; tests `test_get_related_returns_direct_neighbor` (depth=1) and `test_get_related_depth_two_traverses_two_hops` (depth=2) |
| returns entities with relation and citation | result dicts include `relation`, `source_link`, `harvested_at`, `sensitivity`, `confidence`; verified by `test_get_related_citation_fields_present` |

## Not verified
- Docker build and live Postgres recursive CTE execution (no Docker in CI).
- MCP client (Claude Desktop) wire-level interoperability.

## Checks
- 9/9 unit tests pass
- contract-check: no mismatches
- secret-scan: no secrets found
- spec_check: OK (lite verify)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
