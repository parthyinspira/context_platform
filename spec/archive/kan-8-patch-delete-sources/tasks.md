# Tasks

- [x] 1. Add `GET /sources` route + test (scenario: list-sources) - test first
- [x] 2. Add `SourceUpdate` schema (optional `schedule`/`status`, same cron/status validators as `SourceCreate`) + tests for invalid schedule/status (scenarios: patch-invalid-schedule, patch-invalid-status) - test first
- [x] 3. Add `PATCH /sources/{id}` route: apply partial update, 404 on unknown id (scenarios: patch-schedule, patch-status, patch-unknown-source) - test first
- [x] 4. Add `DELETE /sources/{id}` route: set status=disabled, 404 on unknown id (scenarios: delete-soft-disables, delete-unknown-source) - test first
- [x] 5. Docs and contracts updated (none required; schema/ontology unchanged)
- [x] 6. verification.md completed
