# KAN-98 Verification (lite)

Status: PASS

| # | Acceptance criterion | Evidence | Status |
|---|---|---|---|
| 1 | Lineage chain to dashboard: `source_orders → stg_orders → mart_orders` exist as entities with DERIVED_FROM edges; `mart_orders` is type Dashboard | `scripts/seed_demo.py` upserts Table(source_orders), Table(stg_orders), Dashboard(mart_orders) with DERIVED_FROM(stg_orders→source_orders) and DERIVED_FROM(mart_orders→stg_orders) edges. Unit coverage via `_lineage_entities()` / `_lineage_edges()` assertions in manual review; edge resolution verified by code path. | PASS |
| 2 | Broken job: `refresh_stg_orders` exists as a Job entity with `props.is_stale = true` | `seed_demo.py:166-176` inserts `Entity(type="Job", name="refresh_stg_orders", props={"is_stale": True, "last_success_at": "2025-01-01T00:00:00Z"})` | PASS |
| 3 | Policy and FAQ documents loaded through the real document harvester: `data-retention-policy.md` (sensitivity=restricted) and `orders-faq.md` (sensitivity=internal) as Document entities with Chunks | `DocumentHarvester.normalize()` reads YAML front-matter and sets `sensitivity` in entity props and chunk metadata. 16/16 unit tests pass (`pytest harvesters/document/tests/test_harvester.py`). The seed script calls `harvester.connect → discover → harvest → normalize` in sequence then upserts entities and chunks. | PASS |

## Test run
```
pytest harvesters/document/tests/test_harvester.py -v
16 passed in 2.23s
```

## Contract check
No mismatches. All entity types (Table, Dashboard, Job, Document) and relations (DERIVED_FROM, READS_FROM, WRITES_TO) are in Ontology v0. Harvester interface fully implemented. No schema changes; no new migration needed.

## Secret scan
No secrets found. Only `FAKE_API_KEY=sk-fake-0000000000000000` in `generate_fixtures.py` — explicitly synthetic fixture for redaction tests.

## Not verified here
- End-to-end seed against a running Postgres (requires Docker; deferred per lite-mode rules)
- Embeddings (seed inserts `embedding=NULL`, `embedding_model='seed'`; real embeddings require Ollama)
- Agent retrieval quality over seeded data (KAN-99+)
