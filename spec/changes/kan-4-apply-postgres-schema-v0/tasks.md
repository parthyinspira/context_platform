# Tasks

- [x] 1. Write migration test harness: apply from empty, assert tables/columns exist (scenario: fresh database) - test first
- [x] 2. Add `scripts/migrate.py` runner (apply, track in `schema_migrations`, no-op on already-applied) (scenario: idempotent re-run)
- [x] 3. Add migration `0001_core_tables.up.sql` creating `vector` extension + `sources`, `entities`, `edges`, `chunks`, `proposed_changes` per CLAUDE.md columns, with FKs/indexes on `source_id`, `external_id`, `tombstoned_at` (scenario: fresh database, columns match contract)
- [x] 4. Add matching `0001_core_tables.down.sql` dropping the five tables (scenario: rollback)
- [x] 5. Remove/replace `scripts/init-db/001-pgvector.sql` so the extension is created once, by the migration, not by both paths
- [x] 6. Wire migration run into `docker-compose.yml` / README so a fresh `docker compose up` ends with schema applied (document the command if not automatic)
- [x] 7. Run migration test: empty -> apply -> re-apply (no-op) -> rollback -> verify tables gone (scenario: fresh database, idempotent re-run, rollback)
- [x] 8. Verify Confluence Contracts page (section 4.4 of Project Home) matches the migrated schema (scenario: Confluence updated) — already matches column-for-column; no edit needed
- [x] 9. Docs and contracts reviewed for accuracy (CLAUDE.md "Postgres schema v0" already matches the migration; spec/capabilities/postgres-schema.md is applied from the delta at spec-archive, per spec/README.md)
- [ ] 10. verification.md completed
