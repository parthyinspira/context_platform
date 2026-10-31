# Design: migration mechanism for Postgres schema v0

## Decision
Use plain numbered forward/down SQL files under `migrations/` (e.g. `0001_core_tables.up.sql` / `0001_core_tables.down.sql`), applied by a small Python runner script (`scripts/migrate.py`) that tracks applied filenames in a `schema_migrations` table. No external migration library (alembic/yoyo) is introduced.

## Why
- CLAUDE.md asks for "small modules" and no unnecessary dependencies; the existing `scripts/init-db/001-pgvector.sql` already follows a numbered-SQL convention.
- The schema is still v0 with a handful of tables; a full migration framework (with autogeneration, branching migrations, etc.) is more than this stage needs.
- A plain runner is trivial to run identically in compose, CI and cloud (just `psql`/`psycopg` + the SQL files), matching the "no cloud-specific SQL" and container-first rules.

## Alternatives considered
- **alembic**: strong tooling but Python/SQLAlchemy-coupled; adds a dependency and ORM-shaped migration files for what is currently five tables of plain SQL.
- **yoyo-migrations**: lighter than alembic but still an extra dependency for a one-shot v0 schema; revisit if migrations grow complex (branching, data migrations with app logic).

## Open question carried into proposal
`chunks.embedding` dimension is not yet fixed by an `EmbeddingProvider` choice. The migration will use `vector(1536)` as a placeholder; changing the dimension later is itself a new migration (documented as a known follow-up, not blocking this story).
