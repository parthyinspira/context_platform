# Verification

Status: PASS
Date: 2026-10-31   Commit: f5e51b9

## Checks
| Check | Result |
|---|---|
| Lint | No lint tool is configured in this repo yet (no `.flake8`/`ruff.toml`/`pyproject.toml`); `python -m py_compile` on all new modules passed clean |
| Tests (full suite) | PASS — `scripts/tests` 3 passed (`python -m pytest tests -q` from `scripts/`); `api/tests` 1 passed (pre-existing, unaffected) |
| docker compose up exercised | PASS — `docker compose up -d --build`: `postgres`, `migrate`, `api`, `scheduler`, `embeddings` all healthy/exited-0; `ui` failed only on a pre-existing host port 3000 conflict with an unrelated local container, unrelated to this change |
| contract-check | No mismatches: schema has a migration, matches CLAUDE.md "Postgres schema v0" and Confluence Project Home section 4.4 column-for-column; no cloud SDK imports; no secrets in diff; `.env` gitignored |
| Definition of Done | Met: AC demonstrable, tests added and passing, runs from `docker compose up`, no contract changes needed (already aligned), no secrets/cloud SDK violations |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Schema applied by repeatable migrations / fresh database | `scripts/tests/test_migrate.py::test_fresh_database_creates_all_core_tables_with_contract_columns` — PASS. Also manually: `docker compose up -d --build` then `docker compose exec postgres psql -U context -d context -c "\dt"` listed `sources, entities, edges, chunks, proposed_changes, schema_migrations` | PASS |
| Schema applied by repeatable migrations / idempotent re-run | `scripts/tests/test_migrate.py::test_reapplying_migrations_is_a_no_op` — PASS | PASS |
| Schema applied by repeatable migrations / rollback | `scripts/tests/test_migrate.py::test_rollback_drops_core_tables` — PASS. Also manually: `docker compose run --rm migrate down` then `\dt` showed only `schema_migrations`; `docker compose run --rm migrate up` restored all five tables | PASS |
| Schema matches the contract / columns match contract | `EXPECTED_COLUMNS` assertions inside `test_fresh_database_creates_all_core_tables_with_contract_columns` compare every column in CLAUDE.md's "Postgres schema v0" per table — PASS | PASS |
| Schema matches the contract / Confluence updated | Read Confluence page "Context Platform (Hackathon) – Project Home" (id 786433, space SD) section 4.4 "Postgres schema v0" via `getConfluenceContent`; column lists for `sources`, `entities`, `edges`, `chunks`, `proposed_changes` match the migration exactly — no edit required | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Tables `sources`, `entities`, `edges`, `chunks`, `proposed_changes` created by a repeatable migration | fresh database, idempotent re-run, rollback | PASS |
| Schema matches the Confluence Contracts page | columns match contract, Confluence updated | PASS |

## Not verified
- `ui` service health under `docker compose up`: blocked by a pre-existing host port 3000 conflict with an unrelated local container on this machine, not by anything in this change. `postgres`, `migrate`, `api`, `scheduler` all verified healthy with the schema applied.
