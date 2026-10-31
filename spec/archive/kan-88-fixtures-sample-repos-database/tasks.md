# Tasks

- [x] 1. Write `scripts/generate_fixtures.py` skeleton with a deterministic, idempotent `main()` that clears and rewrites `fixtures/` (scenario: fixtures-regeneration-deterministic) — test first: `scripts/tests/test_generate_fixtures.py::test_regeneration_is_deterministic`
- [x] 2. Generate `fixtures/repos/sql-dbt-sample/` (source table DDL, staging model, mart model, `schema.yml`) (scenario: sql-dbt-fixture-present)
- [x] 3. Generate `fixtures/repos/java-sample/` (`pom.xml`, `src/main/java/**`, SQL resource, `target/` dummy) (scenario: java-fixture-present)
- [x] 4. Generate `fixtures/repos/dotnet-sample/` (`.sln`, `.csproj`, `.cs`, `appsettings.json`, `bin/`/`obj/` dummy) (scenario: dotnet-fixture-present)
- [x] 5. Generate `fixtures/repos/talend-sample/` (`.item`/`.properties` jobs, oversized dummy binaries/screenshots, one fake-secret placeholder) (scenario: talend-fixture-present, secret-scan-clean)
- [x] 6. Generate `fixtures/repos/shared/scripts/` shell scripts referencing the sample tables, linking the Java/SQL lineage chain
- [x] 7. Generate `fixtures/db/init.sql` (schemas, tables, view, stored procedure, comments, seed rows, one stale table) (scenario: postgres-fixture-present)
- [x] 8. Generate `fixtures/docs/` markdown policy/FAQ docs with sensitivity front matter, plus `fixtures/docs/sample.xlsx` via `openpyxl` (scenario: docs-fixture-present, excel-fixture-present)
- [x] 9. Write `fixtures/EXPECTED.md` documenting expected entities/edges per fixture (scenario: fixtures-documented)
- [x] 10. Write `scripts/tests/test_generate_fixtures.py` covering all scenarios above (presence, size caps, determinism, name cross-references)
- [x] 11. Run `secret-scan` skill over `fixtures/`; confirm only the one documented fake secret is flagged (scenario: secret-scan-clean)
- [x] 12. Run `contract-check` skill: confirm no schema/ontology/harvester-interface/adapter/MCP change in this diff
- [x] 13. Update `spec/capabilities/harvester-framework.md` is NOT touched directly (deltas live in change folder per workflow; applied at archive time)
- [x] 14. `verification.md` completed with evidence per scenario and acceptance criterion
