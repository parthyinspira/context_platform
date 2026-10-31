# Design / spike outcome: SQL lineage extraction with sqlglot

## What was tried
A standalone function, `ontology.sql_lineage.extract_sql_lineage(sql, source_id, ontology_version)`,
parses SQL text statement-by-statement with `sqlglot` (default/generic dialect, no
specific warehouse dialect selected) and emits:
- `Entity(type="Table", ...)` for every table referenced, keyed by `external_id`
  (`schema.table`, or just `table` when unqualified).
- `Edge(relation="READS_FROM", ...)` and `Edge(relation="WRITES_TO", ...)`, both
  from a synthetic `"query"` proxy node representing "this statement" to the
  tables it reads / its write target, respectively. `"query"` is never emitted
  as an `Entity` itself; it is only used as an edge endpoint until a real
  harvester supplies a Job/Module entity to use instead (story-reviewer caught
  an earlier version of this code wiring `WRITES_TO` as a self-loop,
  `table -> table`, instead of `query -> table`; fixed before merge, with a
  regression test asserting `src_entity_id != dst_entity_id`).

Covered statement shapes: `SELECT ... FROM ... JOIN`, `INSERT INTO ... SELECT`,
`UPDATE ... FROM`, `CREATE TABLE ... AS SELECT` (CTAS), `MERGE INTO ... USING`,
and CTEs (the CTE name itself is not emitted as an entity; its base tables are).

## What works well
- sqlglot's AST (`sqlglot.exp`) makes table-level lineage straightforward:
  `statement.find_all(exp.Table)` plus excluding CTE names and the write target
  covers every statement shape tried, with no per-dialect special-casing needed
  for these common forms.
- CTEs resolve cleanly: `exp.CTE` nodes give the alias set to exclude, and the
  CTE's own body still contributes its base tables via the same `find_all` walk.
- Confidence: a flat `0.9` for all deterministic parses is a reasonable default
  (CLAUDE.md: "every fact stores ... confidence"); there was no need for the
  spike to vary it by statement type.

## Limitations found
1. **Script splitting.** `sqlglot.parse()` on a multi-statement script raises
   `ParseError` and drops *all* statements, including valid ones before and
   after the bad one -- this conflicts with the "everything is manifested,
   nothing silently dropped" rule (`docs/HARVESTERS.md` rule 11). The spike
   works around this by splitting the script on `;` ourselves and parsing each
   chunk independently with `sqlglot.parse_one(..., error_level=RAISE)`
   (the default), so one bad statement is reported in `unparsed` without
   hiding the others. **Known gap:** naive `;` splitting breaks on semicolons
   inside string literals, comments, or stored-procedure bodies (T-SQL
   `BEGIN...END`, PL/pgSQL `DO $$...$$`). A production harvester should use a
   dialect-aware statement splitter (sqlglot does not expose a public
   "tolerant split" API as of 25.32.1) or run per-file (one file = one
   statement) rather than per-script where practical.
2. **Dialect selection.** No `dialect=` was passed to sqlglot (generic/ANSI
   mode). Vendor-specific syntax (e.g. T-SQL `OUTPUT`, BigQuery backtick
   identifiers, Snowflake `QUALIFY`) was not tested and will likely need an
   explicit `dialect` parameter per source once a real harvester supplies one
   (git repo stack detection, or a source config field).
3. sqlglot's parser is lenient on some garbage input under `error_level=IGNORE`
   (not used by this spike's default `RAISE` mode, but tried during
   exploration): a statement like
   `SELEKT * FORM not sql at all` does not always raise -- it may parse into a
   nonsensical but "valid" expression tree (e.g. an `Alias`/`Not`/`Mul` chain)
   with no tables found, silently producing zero entities/edges rather than an
   `unparsed` entry. This spike did not find a reliable way to detect "parsed
   but nonsensical" versus "legitimately has no table references" (e.g.
   `SELECT 1`) without added heuristics -- flagged as a follow-up, not solved
   here.
4. **No entity-id resolution.** The extractor returns `external_id` strings
   (`schema.table`) as `src_entity_id`/`dst_entity_id` on edges, not real
   `entities.id` UUIDs, because there is no entity store to resolve against in
   this spike. A harvester's `normalize()` step must resolve `external_id` ->
   `entities.id` (by `source_id` + `external_id`, matching the `UNIQUE
   (source_id, external_id)` constraint in migration `0001_core_tables`) before
   upserting rows into `edges`.
5. **Table-level only.** Column-level lineage (sqlglot also supports this via
   `sqlglot.lineage`) was out of scope for this spike and for Ontology v0's
   `READS_FROM`/`WRITES_TO` relations, which are table-to-table.

## Recommendation for Epic 5 (ontology updater)
- **Adopt `sqlglot` for deterministic SQL lineage.** It covers the common
  statement shapes needed for the Git/SQL harvesters' `normalize()` step with
  little custom code, matching CLAUDE.md's "deterministic extraction first ...
  SQL lineage via sqlglot."
- When wiring into a harvester: parse **one file/object at a time** rather than
  whole scripts where the source allows it (matches "chunk by structure" in
  CLAUDE.md), to sidestep the script-splitting limitation above entirely.
- Pass an explicit `dialect` once the harvester's stack-detection (per
  `docs/HARVESTERS.md` "Source-specific scoping: Git") can supply one (e.g.
  detect Snowflake/T-SQL/Postgres from repo markers or source config).
- Resolve `external_id` -> `entities.id` in the normalizer (upsert tables as
  entities first, then edges), not in the extractor -- keeps
  `ontology/sql_lineage.py` a pure, DB-free function that stays easy to test.
- Table-level lineage is enough for Ontology v0; column-level lineage
  (`sqlglot.lineage`) is a reasonable later enhancement, not needed for the
  current `READS_FROM`/`WRITES_TO` relations.
