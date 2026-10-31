# Tasks

- [x] 1. Add `ontology/` package skeleton (`__init__.py`, `requirements.txt` with `sqlglot`, `requirements-dev.txt` with `pytest`/`ruff`, `tests/__init__.py`) (scenario: reads-from-select) - test first: failing import test before the module exists
- [x] 2. Implement `Entity`/`Edge`/`LineageResult` dataclasses and `extract_sql_lineage()` for single `SELECT` statements -> `READS_FROM` edges (scenario: reads-from-select) - test first
- [x] 3. Extend `extract_sql_lineage()` for `INSERT INTO ... SELECT` and `UPDATE ... FROM` -> `WRITES_TO` + `READS_FROM` edges (scenario: writes-to-insert-select) - test first
- [x] 4. Extend for `CREATE TABLE ... AS SELECT` (CTAS) and `MERGE INTO ... USING` (scenario: writes-to-ctas) - test first
- [x] 5. Handle CTEs (resolve to base tables, not emitted as entities) and multi-statement scripts, with an `unparsed` list for statements sqlglot cannot parse (scenario: multi-statement-script) - test first
- [x] 6. Add fixtures under `ontology/fixtures/*.sql` covering each scenario above
- [x] 7. Write `design.md`: spike findings (dialects tried, what parses cleanly, known failure modes) and a recommendation for Epic 5 (scenario: spike-outcome-doc)
- [x] 8. Add `ontology` to the CI `test-python` matrix in `.github/workflows/ci.yml` and to the `ruff` `include` list in `pyproject.toml`
- [x] 9. Docs and contracts updated: new `spec/capabilities/sql-lineage-extraction.md` delta only (no schema/ontology-relation-set/harvester-interface change; no Confluence Contracts edit needed)
- [x] 10. `verification.md` completed with evidence per scenario
