# KAN-48 Verification (lite)

| # | Acceptance criterion | Status | Evidence |
|---|----------------------|--------|----------|
| 1 | Depth-limited traversal over READS_FROM/WRITES_TO/DERIVED_FROM using recursive CTE | PASS | `_DOWNSTREAM_CTE` and `_UPSTREAM_CTE` in `routes_lineage.py` use `WITH RECURSIVE lineage` with `depth < max_depth` guard; `test_downstream_returns_job_and_dashboard` and `test_upstream_returns_table_for_job` confirm traversal in both directions |
| 2 | Returns path with citations (source link, harvested_at, sensitivity) | PASS | `LineageNodeOut` carries `source_link`, `harvested_at`, `sensitivity`; joined from `sources` and latest `chunks` in the CTE; `test_lineage_nodes_include_citations` verifies all three fields |
| 3 | Tombstoned entities excluded | PASS | CTE JOINs `entities` with `AND ent.tombstoned_at IS NULL`; start-entity check also filters tombstoned (returns 404); `test_returns_404_when_start_entity_tombstoned` and `test_tombstoned_entity_not_in_lineage_results` verify both cases |

## Test run
```
api/tests/test_lineage.py  7 passed
api/ (full suite)          54 passed, 0 failed
```

## Checks
- secret-scan: no secrets found
- contract-check: no mismatches
- spec_check: OK (lite plan)

Status: PASS
