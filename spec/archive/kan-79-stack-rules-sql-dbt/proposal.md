# KAN-79: Stack rules: SQL/dbt, Java, .NET, Talend, shell, docs

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-79   Epic: KAN-74 Epic 10: Harvester framework - planning, scoping, validation   Branch: kepler/kan-79-stack-rules-sql-dbt

## Why
`docs/HARVESTERS.md` section 4 already documents, per stack, which files a Git harvester should pull and skip (SQL/dbt, Java, .NET, Talend, shell/scripts, docs), and `spec/archive/kan-76-harvest-plan-model-budget` delivered the shared `HarvestPlan`/`Budgets` model that carries include/exclude globs and caps. No code turns that table into actual rules yet. This story delivers the YAML rule files and a loader that builds a `HarvestPlan` per stack, so the future Git harvester's `plan()` step (Epic 3, not yet built) has ready-made, tested rules to apply, matching the precedent set by `spec/archive/kan-76-harvest-plan-model-budget` (framework built ahead of the harvester that will call it).

## What changes
- Add `harvesters/rules/{sql_dbt,java,dotnet,talend,shell,docs}.yaml`: one YAML file per stack with `include`, `exclude` glob patterns and `size_cap_bytes`, matching the pull/skip columns in `docs/HARVESTERS.md` section 4.
- Add `harvesters/framework/stack_rules.py`: `load_stack_rules(stack) -> HarvestPlan` (reads the YAML, merges a shared `COMMON_EXCLUDE` list for `.git`, `node_modules`, vendor folders, lock files, media and archives per `docs/HARVESTERS.md` rule 5, and returns a `HarvestPlan`), `available_stacks() -> tuple[str, ...]`, and `UnknownStackError`.
- Add `harvesters/tests/test_stack_rules.py`: one test per stack confirming its rules keep the expected files and drop the expected ones, run against the existing fixture repos (`fixtures/repos/{sql-dbt,java,dotnet,talend}-sample`) delivered by `spec/archive/kan-88-fixtures-sample-repos-database`, plus the fixture test required by the acceptance criteria — the Talend fixture plans only its `.item`/`.properties` files and nothing else (jar, screenshot, project marker, README all excluded).
- Add `pyyaml` to `harvesters/requirements.txt` (first YAML parsing need in this package).
- Spec delta: add a "Stack rules" requirement to `spec/capabilities/harvester-framework.md`.

## In scope
- The six stack rule files and the loader (pure, no I/O beyond reading the YAML files, no cloud SDK, no LLM).
- Tests against the existing fixture repos proving include/exclude/caps behavior, including the Talend-only-item-and-properties scenario named in the AC.

## Out of scope
- Any actual harvester (`connect`/`discover`/`profile`/`harvest`/`normalize`/`validate`) or stack *detection* from marker files (`pom.xml`, `*.sln`, `talend.project`, etc.) — Epic 3 (Git harvester) is not built yet; this story is the rules a future `plan()` step will look up once it has detected a stack.
- LLM-assisted plan refinement (`docs/HARVESTERS.md` section 6, `skills/*.md`) — deterministic rules only.
- New or changed fixtures — the fixture repos already exist (`spec/archive/kan-88-fixtures-sample-repos-database`); this story only adds rules and tests that read them.
- Budget enforcement behavior — already delivered by `spec/archive/kan-76-harvest-plan-model-budget`; this story only sets `size_cap_bytes` per stack on the plans it builds.

## Acceptance criteria (from Jira)
1. YAML rules per stack with include/exclude and caps -> scenarios: stack-rules-loaded-per-stack, each-stack-plan-holds-size-cap
2. Fixture tests prove a Talend-like repo plans only .item/.properties files -> scenario: talend-fixture-plans-only-item-and-properties

## Affected
Capabilities: spec/capabilities/harvester-framework.md (adds a "Stack rules" requirement)   Docs/contracts: none (`docs/HARVESTERS.md` section 4 already documents this table; no schema/ontology/harvester-interface change)

## Risks and open questions
- Rules live at the shared `harvesters/rules/` path rather than inside a per-source-system pack (`harvesters/<system>/rules/` per `docs/HARVESTERS.md` section 2), because no harvester pack exists yet — same precedent as KAN-76. When the Git harvester pack is built (Epic 3), it is expected to call `harvesters.framework.stack_rules.load_stack_rules(stack)` after detecting the stack, rather than duplicating rules under its own pack folder.
- Stack *detection* (marker-file sniffing) is a separate, not-yet-built concern; these rules assume the caller already knows which stack applies.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
