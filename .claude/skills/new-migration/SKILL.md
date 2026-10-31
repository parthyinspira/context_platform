---
name: new-migration
description: Create a Postgres schema migration. Use for any table, column, index or extension change; schema changes are only allowed through migrations.
---

Paths follow the repo layout (default `migrations/`); if the layout differs, follow the actual one.

1. Confirm the change is in the approved proposal and spec delta. If not, stop.
2. Create a numbered, forward migration and a matching rollback (down) migration. One concern per migration; never edit an applied migration.
3. Keep SQL portable Postgres + pgvector only (no cloud-specific SQL). Record `embedding_model` on chunk-related changes; keep `source_id`, `external_id`, `tombstoned_at`, `ontology_version` conventions.
4. Add a migration test: apply from empty, apply to the previous version with data, roll back, re-apply.
5. Update the "Postgres schema" section in `CLAUDE.md`, the relevant `spec/capabilities/*.md` delta, and note the Confluence Contracts page needs the same change.
6. Run the `contract-check` skill; fix any mismatch.
