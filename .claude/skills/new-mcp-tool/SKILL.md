---
name: new-mcp-tool
description: Scaffold a new MCP tool, resource or prompt for the retrieval or admin MCP servers with citations, sensitivity filtering, token budgets and tests.
---

Read `docs/ARCHITECTURE.md` section 3 and `spec/capabilities/mcp-retrieval.md` first.

1. Decide the server: read-only tools go on `context-retrieval`; anything that writes goes on `context-admin` (restricted, audit-logged). Never mix them.
2. Write a clear tool description: what it does and when to use it versus other tools. Keep the tool surface small.
3. Inputs validated; outputs always include source link, `harvested_at` and `sensitivity` (and `confidence` where relevant); label results `indexed` or `live`.
4. Enforce caller identity: filter by sensitivity and source access; restricted sources never appear in results or error text. Exclude tombstoned entities.
5. Token budget: truncate or paginate with `next_cursor`.
6. Audit-log the call (caller, tool, query, returned source IDs) without logging sensitive content.
7. Tests: happy path, empty result, restricted source, tombstoned entity, pagination, budget cap. Add scenarios to the spec delta.
8. Update `docs/ARCHITECTURE.md` MCP section if the tool list changes.
