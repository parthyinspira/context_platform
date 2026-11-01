# Verification: KAN-33 MCP tool get_related(entity)

Status: PASS

## AC evidence

### AC1: traverses edges (depth-limited) via recursive CTE
- `mcp_server/tools/get_related.py` implements `_CTE_SQL` — a `WITH RECURSIVE traverse(…)` CTE that seeds from the start entity and recursively extends up to `depth` hops, bounded by `WHERE t.depth < %(depth)s`.
- Tests `test_get_related_returns_direct_neighbor` (depth=1 → only e2) and `test_get_related_depth_two_traverses_two_hops` (depth=2 → e2 and e3) verify depth limiting.
- Test `test_get_related_direction_out_only` / `test_get_related_direction_in_only` verify direction filtering.

### AC2: returns entities with relation and citation
- `get_related` returns a list of dicts with keys: `entity_id`, `type`, `name`, `source_id`, `relation`, `confidence`, `source_link`, `sensitivity`, `harvested_at`.
- Test `test_get_related_citation_fields_present` asserts all citation fields are present in every result row.

## Scenario verification
| Scenario | Result |
|---|---|
| depth=1 from e1 → returns {e2} | PASS (test_get_related_returns_direct_neighbor) |
| depth=2 from e1 → returns {e2, e3} | PASS (test_get_related_depth_two_traverses_two_hops) |
| tombstoned entity excluded | PASS (test_get_related_excludes_tombstoned) |
| relation filter restricts edges followed | PASS (test_get_related_relation_filter) |
| non-existent entity → empty list, no error | PASS (test_get_related_nonexistent_entity_returns_empty) |
| direction=out / direction=in | PASS (test_get_related_direction_out_only / _in_only) |
| citation fields present | PASS (test_get_related_citation_fields_present) |

## Test run
```
9 passed in 0.06s
```

## Contract check
No schema changes, no ontology changes, no harvester interface changes. MCP tool signature matches ARCHITECTURE.md. No cloud SDK imports outside adapters/. spec/capabilities/mcp-retrieval.md updated with get_related requirement.

## Secret scan
No secrets found. `.env` untracked, `.env.example` has placeholder values only.

## spec_check
`spec_check OK (lite plan)`

## Not verified
- Docker build and live Postgres recursive CTE execution (no Docker in CI).
- MCP client interoperability (Claude Desktop JSON-RPC wire format) not tested end-to-end.
- `DISTINCT ON` behaviour in the live Postgres CTE (the fake uses BFS, not SQL).
