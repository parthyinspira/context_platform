# Harvester design: scoping, skills, rules and validation

Harvesters are the most important part of the platform. They must pull what matters, not everything, and prove that they did.

## 1. Lifecycle (every source type)

```
Connect -> Discover -> Profile -> Plan -> (approve) -> Harvest -> Validate -> Publish | Quarantine
```

| Stage | What happens | Output |
|---|---|---|
| Connect | Test credentials with a read-only identity | ok / error |
| Discover | List what is available at the source, metadata only: repos, branches, databases, schemas, sites, libraries, workbooks | scope tree shown in the UI |
| Profile | Cheap scan of the chosen scope: sizes, file-type counts, detected stacks, row counts | profile report |
| Plan | Rules (and optionally an LLM following the harvester's skills) turn the profile into a **harvest plan**: include/exclude patterns, caps, budgets | plan the user approves in the UI |
| Harvest | Execute the plan incrementally using the cursor | raw objects + manifest |
| Validate | Run the harvester validator against the plan and manifest | pass / warn / fail |
| Publish / Quarantine | Pass: normalize and update the graph. Fail: keep previous knowledge and show why | run state |

Run states in `harvest_runs`: `CONNECTING, DISCOVERING, PROFILING, PLANNED, APPROVED, HARVESTING, VALIDATING, PUBLISHED, QUARANTINED, FAILED`.

The harvester is "built" on first use by generating the **plan** from the profile. We generate configuration, not code, at runtime. New source *types* are added at development time (see section 6).

## 2. Harvester pack (one folder per source system)

```
harvesters/<system>/
  harvester.yaml      # capabilities, credential fields, discoverable scope types, default limits
  harvester.py        # connect, discover, profile, fetch, normalize (implements the interface)
  rules/              # deterministic include/exclude and limits (YAML)
  skills/             # markdown guidance an LLM follows to propose or refine the plan
  validator.py        # checks specific to this system
  fixtures/           # sample data used by tests
```

### Interface (extends the contract in CLAUDE.md)
```python
class Harvester:
    def connect(self, creds) -> ConnectionResult
    def discover(self, conn) -> ScopeTree               # list-only, no content
    def profile(self, conn, scope) -> Profile           # sizes, counts, stacks
    def plan(self, profile, rules) -> HarvestPlan       # include/exclude, caps, budgets
    def harvest(self, conn, plan, cursor) -> Iterable[RawObject]
    def normalize(self, raw) -> list[Entity | Edge | Chunk]
    def validate(self, plan, manifest, results) -> ValidationReport
```

## 3. Rules that apply to all harvesters
1. **Discover before download.** List and size first; fetch only what the plan allows.
2. **Metadata first.** Pull structure (schemas, signatures, config), not bulk data. Row data and Excel cell data are off by default; samples are opt-in with small caps.
3. **Budgets per run.** Maximum files, bytes, wall time, LLM tokens and objects per type. On hitting a budget, stop cleanly, mark the run `PARTIAL` and report what was skipped.
4. **Size caps per object** (default 1 MB for text files; larger files are skipped and listed in the manifest).
5. **Allowlist by purpose, denylist by noise.** Include extensions that carry meaning for the detected stack; always exclude binaries, archives, media, build output and dependencies.
6. **Incremental by default.** Cursor per source (commit SHA, delta token, `last_ddl_time`, modified-since); never refetch unchanged objects.
7. **Read-only.** Read-only credentials; never write to a source.
8. **Secrets and PII.** Scan fetched text for secrets (keys, tokens, passwords) and redact before storing; record a `sensitivity` on each object.
9. **Deterministic first, LLM second.** Use parsers where possible (sqlglot, XML parsers, manifest readers). Use an LLM only for unstructured text, with citations.
10. **Idempotent and resumable.** Re-running the same plan gives the same result; an interrupted run resumes from the manifest.
11. **Everything is manifested.** Every discovered, fetched, skipped and failed object is recorded with a reason. The validator depends on this.
    Implementation: `harvesters/framework/manifest.py` (`Manifest`, `ManifestStore`). One JSON object per run at ObjectStore key `manifests/<source_id>/<run_id>.json`: `{format_version: 1, source_id, run_id, entries: [{ref, discovery_reason, discovered_at, size_bytes, outcome: fetched|skipped|failed|null, outcome_reason, outcome_at}]}`. An object must be discovered before it gets an outcome, and it gets at most one outcome. Reasons are redacted by the shared scanner. Loading enforces the same rules. The validator reads `by_outcome()`, `counts()` and `unaccounted()`.

## 4. Source-specific scoping

### Git
- **Do not clone fully.** Use `git clone --filter=blob:none --sparse` (partial clone) or list files with `git ls-tree -r -l` to get sizes first, then fetch only the planned paths. Shallow depth by default.
- **Detect stacks** from marker files, then apply that stack's rules:

| Stack | Detected by | Pull | Skip |
|---|---|---|---|
| SQL / dbt | `*.sql`, `dbt_project.yml` | DDL, views, procedures, models, `schema.yml` | seed CSVs, large data scripts |
| Java | `pom.xml`, `build.gradle` | build files, `src/main/**/*.java`, configs, SQL resources | `target/`, `*.jar`, `*.class`, `src/test` (optional) |
| .NET | `*.sln`, `*.csproj` | project files, `*.cs` in source projects, `appsettings*.json`, SQL | `bin/`, `obj/`, `*.dll`, packages |
| Talend | `talend.project`, `*.item`, `*.properties` | job `.item` XML (components, connections, context), `.properties` metadata | `*.screenshot`, `*.jar`, generated code, libs, binaries |
| Shell / scripts | `*.sh`, `*.ps1`, `*.bat` | scripts under size cap | logs, outputs |
| Docs (any repo) | `README*`, `docs/**`, `*.md` | text under size cap | images, generated docs |

- Always skip: `.git`, `node_modules`, vendor folders, lock files, minified files, binaries, media, archives.
- Example: a 10 GB Talend repo is mostly screenshots, jars and generated code. The plan selects only `.item` and `.properties` files, which is a small share of the bytes, and the profile shows the user the estimate before approval.
- Entities from Git: Repository, Module, Job, Table (from SQL), Person/Team (from CODEOWNERS); edges READS_FROM/WRITES_TO/DEPENDS_ON from parsed SQL and job definitions.

### SQL database (and Snowflake)
- After credentials: **list databases, then schemas, then objects**; the user ticks what to pull.
- Pull metadata from `information_schema` / catalog views: tables, columns, types, keys, views, stored procedure definitions, row counts, comments. Snowflake: `INFORMATION_SCHEMA` plus `ACCOUNT_USAGE` (e.g. `ACCESS_HISTORY`, query history) for lineage.
- No row data by default. Optional capped samples (for example 5 rows) behind an explicit toggle.
- Cursor: last DDL time or schema hash; tombstone dropped objects.

### SharePoint
- Discover sites, then libraries, then folders (Microsoft Graph). Use **delta queries** for incremental runs.
- Types: docx, pdf, pptx, md, txt as documents (chunked by section); xlsx as structure only (sheet names, headers, named ranges, formulas summary, capped sample rows); skip media and archives.
- Size cap per file; skip over-large files and list them.

### Tableau
- Use the REST and Metadata (GraphQL) APIs: sites, projects, workbooks, views, data sources, fields, and upstream tables. No extract data.
- Edges: Dashboard READS_FROM data source / Table; owner from the workbook.

## 5. Harvester validator

Runs after every harvest and before anything is published to the graph.

| Check | What it verifies | On failure |
|---|---|---|
| Completeness | Every in-scope object in the plan is fetched, skipped (with reason) or failed (with reason); fetched / planned ratio above a threshold | warn or fail |
| Exclusion integrity | No excluded type or path was fetched | fail |
| Budget compliance | Files, bytes, time and token budgets respected | warn (run marked PARTIAL) |
| Parse success | Share of files parsed without errors above a threshold, per type | warn or fail |
| Expected yield | Detected stack yields the expected entities (SQL files give Tables, Talend `.item` gives Jobs, etc.); zero yield is a failure | fail |
| Ontology conformance | Every emitted entity and edge uses a known type and has `source_id`, `external_id`, `harvested_at`, `ontology_version` | fail |
| Referential integrity | Edges point to existing entities (or are queued as unresolved) | warn |
| Delete sanity | A spike of tombstones (for example more than 20 percent of objects) is not applied automatically | quarantine |
| Secrets / PII | No detected secrets stored; sensitivity set | fail if secrets found unredacted |
| Freshness | `harvested_at` and cursor advanced | warn |
| Spot check (optional) | A sample of objects re-fetched and compared to what was stored | warn |

Output: a `ValidationReport` with status `PASS | WARN | FAIL`, check results, counts and sample failures. `FAIL` quarantines the run (previous knowledge stays); `WARN` publishes and shows a warning in the UI.

## 6. Skills and rules (how we build and guide harvesters)

- **Rules** (`rules/*.yaml`): deterministic include/exclude, caps and budgets, per stack and per source type. Versioned; changes need a test.
- **Skills** (`skills/*.md`): short guidance an LLM follows when profiling or planning (for example "how to recognize a Talend project", "which files hold the job logic", "what to do when the repo is over budget"). Each skill lists inputs, steps and a required output schema.
- **Claude Code skill `new-harvester`** (development time): scaffolds a new harvester pack from this contract: `harvester.yaml`, interface stubs, a rules template, a validator with the standard checks, fixtures and a test. Use it for every new source system.
- Plans produced by an LLM are validated against the rules (caps and denylists always win) before they are shown to the user.

## 7. Tests for each harvester
- Fixture source (small sample repo, sample database, sample documents).
- Plan test: expected include/exclude decisions on the fixture.
- Re-run test: idempotent, no duplicates; incremental run only touches changes.
- Validator test: deliberately broken fixtures (missing files, oversize file, secret in file, delete spike) produce the right `WARN` / `FAIL`.

## 8. Running a harvest (one-off container job)

`harvesters/run.py` (image entrypoint `python -m harvesters.run`) drives one registered
`Harvester` end to end for an already-planned run: `connect -> discover -> harvest ->
normalize -> validate`, writing each state transition to `harvest_runs`, deciding
publish-vs-quarantine with `harvest_validation.PublishQuarantineGate`, and publishing
`harvest.completed` on the `EventBus`.

Configuration is environment-variable only, so the same image runs unmodified as:
- a local one-off container: `docker compose run --rm -e SOURCE_ID=<id> -e PLAN_ID=<id> harvester`
- a GCP Cloud Run Job (per-execution env vars set on the job/execution)
- an Azure Container Apps Job (per-execution env vars on the job trigger)

| Variable | Required | Meaning |
|---|---|---|
| `SOURCE_ID` | yes | the `sources.id` to harvest (CLI override: `--source-id`) |
| `PLAN_ID` | yes | the `harvest_runs.id` of an already `PLANNED`/`APPROVED` row — its `plan` JSONB column holds the `HarvestPlan` (CLI override: `--plan-id`); no separate `plans` table exists |
| `DATABASE_URL` | yes | Postgres connection string, same as `api`/`scheduler` |
| `SECRET_STORE`, `EVENT_BUS` | no | adapter selection, same keys as `adapters/factory.py` |

Exit codes: `0` when the run reached `PUBLISHED` or `QUARANTINED` (the lifecycle completed
and the gate made a decision), `1` when it ended `FAILED` (connect error or unhandled
exception), `2` when it could not start (missing `SOURCE_ID`/`PLAN_ID`/`DATABASE_URL`, or
an unknown `PLAN_ID`) — nothing is written to `harvest_runs` in the `2` case.

Persisting the `Entity`/`Edge`/`Chunk` records `normalize()` produces to Postgres is the
job of a separate, future normalizer consuming `harvest.completed`, not this runner (see
`CLAUDE.md`'s flow); the runner only counts them for the published event's payload.
