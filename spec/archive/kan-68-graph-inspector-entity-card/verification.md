# Verification (lite)

Status: PASS
Date: 2026-10-31   Commit: (working tree on kepler/kan-68-graph-inspector-entity-card)

| Acceptance criterion | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Properties | `api/tests/test_entity.py::test_entity_returns_props_edges_grouped_citations_owner` asserts `body["props"] == {"language": "python"}`; `ui/test/EntityCard.test.jsx` "renders properties..." asserts `entity-prop-language`/`entity-prop-stars` | PASS |
| Edges grouped by relation | Same api test asserts `edges_by_relation` keyed by `DEPENDS_ON`/`CONTAINS` with direction; same ui test asserts `entity-relation-DEPENDS_ON`/`entity-relation-CONTAINS` | PASS |
| Citations (source link, harvested_at, run id) | Same api test asserts `citations == [{"source_link": ..., "harvested_at": ..., "run_id": "run-early"}]`; `test_entity_citation_run_id_null_when_no_run_matches` covers the no-match case; ui test asserts `citation-chip` contains the link, timestamp and run id (or "unknown run") | PASS |
| Owner | Same api/ui tests assert `owner`/`entity-owner` == `alice@acme.com` | PASS |
| Open in source | Same api test asserts `source_uri`; ui test asserts `open-in-source` link `href` equals the source uri | PASS |

Commands run:
- `python -m pytest api -q` -> 47 passed
- `npx vitest run` (ui) -> 20 files, 96 passed
- `ruff check api/` -> all checks passed
- `python scripts/spec_check.py spec/changes/kan-68-graph-inspector-entity-card --stage=verify` -> OK
- `contract-check` skill: no mismatches (no schema/ontology/adapter/MCP changes; `spec/capabilities/ui.md` updated in this PR alongside the behaviour it describes)
- `secret-scan` skill: no secrets found; only `.env.example` tracked

Not verified:
- `EntityCard` is not exercised inside a live force-directed graph canvas/inspector panel — no such screen exists in `ui/` yet (tracked as separate graph-canvas work; out of scope per `plan.md`). Verified standalone against the AC, which names only the entity card.
- `docker compose up` was not run: this change only adds a route to the existing `api` service and a UI component; neither the compose file nor service wiring changed.
- Chunk-to-run attribution (`run_id`) is a best-effort match (latest `harvest_runs` row at/before the chunk's `harvested_at`) because `chunks` has no `run_id` column; this is a known limitation documented in `plan.md`, not a test gap.
