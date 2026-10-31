# KAN-88: Fixtures: sample repos, database and documents

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-88   Epic: 1 Foundation   Branch: kan-88-fixtures-sample-repos-database

## Why
Every harvester (Epics 3-7) needs fixtures to test against per `docs/HARVESTERS.md` section 7 ("Tests for each harvester: Fixture source (small sample repo, sample database, sample documents)") and `CLAUDE.md` ("Tests for every harvester (fixture repos/docs) and for idempotent re-harvest"). None exist yet. This story generates deterministic, non-sensitive demo/test fixtures once, reused by later harvester and MCP stories, so those stories do not each invent their own ad hoc test data. The `demo-data` skill already describes the target shape; this story turns that into generated, committed, documented fixtures.

## What changes
- Add a deterministic generator script `scripts/generate_fixtures.py` that writes everything under `fixtures/`.
- Add `fixtures/repos/sql-dbt-sample/`: a small dbt-style repo (source table -> staging model -> mart model, `schema.yml`).
- Add `fixtures/repos/talend-sample/`: a Talend-like repo with a few `.item`/`.properties` job files plus deliberately large dummy binaries/screenshots, so a scoping plan must skip them.
- Add `fixtures/repos/java-sample/`: a small Maven project (`pom.xml`, `src/main/java/**`, a SQL resource, a `target/` folder to be ignored) including one shell script that reads/writes the sample tables.
- Add `fixtures/repos/dotnet-sample/`: a small .NET project (`*.sln`, `*.csproj`, `*.cs`, `appsettings.json`, a `bin/`/`obj/` folder to be ignored).
- Add `fixtures/repos/shared/scripts/`: shell scripts reading/writing the sample Postgres tables, referenced by the Java and SQL repos' lineage chain.
- Add `fixtures/db/init.sql`: schema + seed for a sample Postgres database (schemas, tables, a view, a stored procedure, comments, row counts) matching the dbt lineage chain, ending in a dashboard-like reporting view; one upstream job/table marked as stale ("broken") for prod-support test scenarios.
- Add `fixtures/docs/`: policy and FAQ documents (`.md`, and one generated `.docx`/`.pdf` if cheaply producible without new heavy deps — otherwise `.md` only, documented as a gap) and one Excel file (`.xlsx`, via `openpyxl`, already available in the environment) with sheet names, headers and a couple of sample rows; one document marked `internal` and one marked `restricted` in front-matter metadata for sensitivity tests.
- Add `fixtures/repos/talend-sample/jobs/*.item` containing one obviously-fake secret string (e.g. `FAKE_API_KEY=sk-fake-0000000000000000`) to exercise future redaction tests; `secret-scan` run over the fixture tree must flag only this one known, clearly-fake value and nothing else.
- Add `fixtures/EXPECTED.md` documenting, per fixture, the entities/edges a harvester should eventually extract (Repository, Module, Table, Column, Job, Document, Person/Team) and the lineage chain, so tests and evals can assert against it.
- Add `scripts/tests/test_generate_fixtures.py`: regenerating the fixtures is deterministic (byte-identical) and produces the documented file layout; asserts the large Talend binaries exceed the 1 MB size-cap mentioned in `docs/HARVESTERS.md` (so a future plan must skip them) and that the dbt/SQL lineage chain files reference each other by name.

## In scope
- Static, synthetic fixture data and the generator script that produces it, plus a smoke test that fixtures exist, are internally consistent (names referenced across files match) and regeneration is deterministic.
- `fixtures/EXPECTED.md` as the documented contract future harvester tests assert against.
- One deliberately oversized/binary-like file set (Talend) and one deliberately "broken" (stale) job, per the issue's implied need for harvester scoping/validation tests (`docs/HARVESTERS.md` section 7).
- One clearly-fake secret value for future redaction-test fixtures (`docs/HARVESTERS.md` rule 8), verified by `secret-scan` to be the only hit.

## Out of scope
- Any actual harvester implementation (`harvesters/<system>/harvester.py`, rules, validator) — those are separate Epic 3/7 stories; this story only supplies the data they will be tested against.
- Loading `fixtures/db/init.sql` into the running Postgres container via compose/migrations — wiring the compose `postgres` service to seed from this file is left to the harvester story that first needs a live sample database (no AC in KAN-88 requires a running container, only "a sample Postgres database" as fixture SQL).
- Generating real `.docx`/`.pdf` binaries if that requires adding a new heavy dependency not already present; falls back to Markdown-only docs with the gap documented, decided during development based on what's already available in `scripts/requirements*.txt`.
- Any UI, API, ontology or schema change — this is fixtures-only.

## Acceptance criteria (from Jira KAN-88)
1. Small, non-sensitive sample SQL repo exists -> scenario: sql-dbt-fixture-present
2. Small, non-sensitive sample Java repo exists -> scenario: java-fixture-present
3. Small, non-sensitive sample .NET repo exists -> scenario: dotnet-fixture-present
4. Small, non-sensitive sample Talend-like repo exists -> scenario: talend-fixture-present
5. A sample Postgres database (schema + seed data) exists -> scenario: postgres-fixture-present
6. Sample docs exist -> scenario: docs-fixture-present
7. Sample Excel files exist -> scenario: excel-fixture-present
8. All fixtures are non-sensitive (no real secrets/PII) -> scenario: secret-scan-clean

## Affected
Capabilities: `spec/capabilities/harvester-framework.md` (ADDED: fixtures requirement)   Docs/contracts: none (no schema/ontology/harvester-interface change); no Confluence Contracts update needed.

## Risks and open questions
- `.docx`/`.pdf` generation may need a dependency not yet in `scripts/requirements*.txt`; resolved during development by checking what's available and falling back to Markdown if adding a new dependency would be out of scope for a fixtures-only story.
- The sample Postgres database is delivered as SQL fixtures (`fixtures/db/init.sql`), not as a running, compose-wired service; a future harvester story will do the wiring. Flagged here so the PR reviewer and verification note this interpretation of AC 5.

## Approval
Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
