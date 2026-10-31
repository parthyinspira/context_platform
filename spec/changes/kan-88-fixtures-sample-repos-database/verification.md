# Verification

Status: PASS
Date: 2026-10-31

## Checks
| Check | Result |
|---|---|
| Lint | No linter configured for `scripts/**` (ruff config covers `api/`, `scheduler/`, `adapters/` only); not applicable |
| Tests (full suite) | `python -I -m pytest scripts/tests/test_generate_fixtures.py -q` -> 9/9 passed |
| contract-check | No schema, ontology, harvester-interface, adapter or MCP changes in this diff; no cloud SDK imports found; not applicable |
| secret-scan | Ran over `fixtures/`, `scripts/generate_fixtures.py`, `scripts/tests/test_generate_fixtures.py`; only hit is the single documented, clearly-fake `FAKE_API_KEY=sk-fake-0000000000000000` placeholder in `fixtures/repos/talend-sample/jobs/load_orders.item`; `.env` untracked, `.env.example` names only |
| Definition of Done | All tasks ticked |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command) | Result |
|---|---|---|
| sql-dbt-fixture-present | `test_sql_dbt_fixture_present` — asserts `models/staging/stg_orders.sql`, `models/marts/mart_orders.sql`, `seeds/source_orders.sql`, `schema.yml` exist and reference each other by name | PASS |
| java-fixture-present | `test_java_fixture_present` — asserts `pom.xml`, `src/main/java/.../OrdersRepository.java`, `src/main/resources/orders.sql`, and a `target/` dummy class exist | PASS |
| dotnet-fixture-present | `test_dotnet_fixture_present` — asserts `.sln`, `.csproj`, `.cs`, `appsettings.json`, and `bin/`/`obj/` dummies exist | PASS |
| talend-fixture-present | `test_talend_fixture_present_with_size_cap_violation` — asserts `.item`/`.properties` job files exist and the dummy screenshot exceeds the 1 MB size cap from `docs/HARVESTERS.md` | PASS |
| postgres-fixture-present | `test_postgres_fixture_present` — asserts `fixtures/db/init.sql` has `CREATE SCHEMA`, `CREATE TABLE`, `CREATE VIEW`, `CREATE OR REPLACE PROCEDURE`, matches the dbt lineage chain, and marks a job stale | PASS |
| docs-fixture-present | `test_docs_and_excel_fixture_present` — asserts policy and FAQ docs exist with `sensitivity: restricted` / `sensitivity: internal` front matter | PASS |
| excel-fixture-present | `test_docs_and_excel_fixture_present` — asserts `fixtures/docs/sample_report.xlsx` exists (generated via `openpyxl`, named sheet, headers, sample rows) | PASS |
| secret-scan-clean | `secret-scan` skill run manually over `fixtures/`; only the one documented fake secret found | PASS |
| fixtures-documented | `test_expected_md_documents_entities` — asserts `fixtures/EXPECTED.md` names Repository/Table/Job/Document entity types | PASS |
| fixtures-regeneration-deterministic | `test_regeneration_is_deterministic` — two runs of `generate()` into separate temp dirs produce byte-identical file trees (including the `.xlsx`, after normalizing its internal zip timestamps) | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| 1. Small, non-sensitive sample SQL repo | sql-dbt-fixture-present | PASS |
| 2. Small, non-sensitive sample Java repo | java-fixture-present | PASS |
| 3. Small, non-sensitive sample .NET repo | dotnet-fixture-present | PASS |
| 4. Small, non-sensitive sample Talend-like repo | talend-fixture-present | PASS |
| 5. Sample Postgres database | postgres-fixture-present | PASS (as a SQL fixture, not a running compose-wired service — see "Not verified") |
| 6. Sample docs | docs-fixture-present | PASS |
| 7. Sample Excel files | excel-fixture-present | PASS |
| 8. All fixtures non-sensitive | secret-scan-clean | PASS |

## Not verified
- **AC 5 interpretation**: `fixtures/db/init.sql` is delivered as a SQL fixture file (schema + seed data), matching `docs/HARVESTERS.md`'s "fixture source (small sample repo, sample database, sample documents)" wording. It has not been loaded into a running, compose-wired Postgres container in this story — that wiring is explicitly out of scope (see `proposal.md`) and left to the harvester story that first needs a live sample database. The SQL was sanity-checked for syntax by inspection, not by executing it against a live Postgres instance (no running Postgres container was exercised in this session).
- **Real `.docx`/`.pdf` fixtures**: only Markdown (`.md`) sample docs were generated, not `.docx`/`.pdf`, since no new dependency was added for that (kept the story fixtures-only, no new runtime deps). Documented as a gap in `proposal.md`; can be added in a follow-up if a later harvester story needs real binary document fixtures.
- **Cross-platform fixture generation**: `scripts/generate_fixtures.py` was run and tested only on Windows in this session; it uses only stdlib `pathlib`/`zipfile`/`shutil` and `openpyxl`, no OS-specific paths, so Linux behavior is expected to be identical but not directly exercised.
