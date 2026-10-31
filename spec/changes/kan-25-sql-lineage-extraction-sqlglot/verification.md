# Verification

Status: PASS
Date: 2026-10-31   Commit: 239a00b291c27ad178c94035a082781a1982690b

## Reviewer round 1
`story-reviewer` ran against commit `955b1cb` and returned CHANGES REQUESTED: one [blocking] finding — `WRITES_TO` edges were self-loops (`src_entity_id == dst_entity_id`), inconsistent with the `READS_FROM` convention and with `design.md`'s own description, and not caught by the original tests (which only asserted `dst`, never `src`). Fixed in commit `239a00b` (`ontology/sql_lineage.py`: `WRITES_TO` now uses the same `"query"` proxy source as `READS_FROM`); added `src != dst` and same-`src` assertions to the relevant tests so it cannot silently regress. Two [nit]s (a stale comment, a statement-as-expression) were also cleaned up. 12/12 tests still pass; lint still clean; see commit `239a00b`.

## Checks
| Check | Result |
|---|---|
| Lint | `python -m ruff check api scheduler adapters ontology --config pyproject.toml` -> All checks passed! |
| Tests (full suite) | `python -m pytest ontology/tests -q` -> 12 passed |
| docker compose up exercised | Not applicable: this is a library-only spike (no new service, no compose change) |
| contract-check | Ran `contract-check` skill against `git diff origin/main...HEAD`: no schema/migration change, no new Ontology v0 entity/relation types (uses existing `Table`/`READS_FROM`/`WRITES_TO`), no harvester-interface implementation claimed, no cloud SDK imports outside `adapters/`, no MCP tool change. No contract changed, so no `CLAUDE.md`/Confluence update required |
| secret-scan | Ran `secret-scan` skill: no keys/tokens/passwords/connection strings found in the diff or fixtures; `git ls-files \| grep -E '\.env($\|\.)'` shows only `.env.example` tracked |
| Definition of Done | All tasks in `tasks.md` ticked |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Deterministic SQL lineage extraction / reads-from-select | `ontology/tests/test_sql_lineage.py::test_select_with_join_yields_reads_from_edges` and `::test_fixture_reads_from_select` (fixture `ontology/fixtures/reads_from_select.sql`) | PASS |
| Deterministic SQL lineage extraction / writes-to-insert-select | `::test_insert_select_yields_reads_from_and_writes_to`, `::test_update_from_yields_reads_from_and_writes_to`, `::test_fixture_writes_to_insert_select` (fixture `writes_to_insert_select.sql`) | PASS |
| Deterministic SQL lineage extraction / writes-to-ctas | `::test_ctas_yields_reads_from_and_writes_to`, `::test_merge_into_yields_reads_from_and_writes_to`, `::test_fixture_writes_to_ctas` (fixture `writes_to_ctas.sql`) | PASS |
| Deterministic SQL lineage extraction / multi-statement-script | `::test_multi_statement_script_reports_unparsed_without_dropping_valid_statements`, `::test_unparseable_single_statement_is_reported_not_raised`, `::test_fixture_multi_statement_script` (fixture `multi_statement_script.sql`); also `::test_cte_resolves_to_base_table_not_emitted_as_entity` for CTE handling | PASS |
| Spike outcome documented / spike-outcome-doc | `spec/changes/kan-25-sql-lineage-extraction-sqlglot/design.md` records what sqlglot handles, limitations found (script splitting, dialect selection, lenient-parse edge case, no entity-id resolution, table-level only), and a recommendation to adopt it in Epic 5 | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| SQL files yield READS_FROM/WRITES_TO edges | reads-from-select, writes-to-insert-select, writes-to-ctas, multi-statement-script (all PASS, 12/12 tests) | PASS |
| Spike outcome documented | spike-outcome-doc (`design.md`) | PASS |

## Not verified
- **Vendor-specific SQL dialects** (T-SQL `OUTPUT`, BigQuery/Snowflake-specific syntax): not exercised in this spike; generic/ANSI dialect only. Documented as a follow-up in `design.md` ("Dialect selection") for when a harvester supplies a dialect.
- **Production wiring into a harvester's `normalize()`**: out of scope per `proposal.md` ("Out of scope") — no `harvesters/` framework exists yet in this repo to wire into.
