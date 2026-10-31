# KAN-76: Harvest plan model and budget enforcement

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-76   Epic: KAN-74 Epic 10: Harvester framework - planning, scoping, validation   Branch: kepler/kan-76-harvest-plan-model-budget

## Why
`spec/capabilities/harvester-framework.md` already requires a `HarvestPlan` with include/exclude rules, caps and budgets, and that a run stop cleanly and be marked `PARTIAL` on hitting a budget (per `docs/HARVESTERS.md` rules 1-3), but no code exists yet — no `harvesters/` package exists at all, since the Git harvester itself (Epic 3) hasn't been built. This story delivers the shared plan model and budget enforcer ahead of any specific harvester, so future harvester packs (Git, SQL, SharePoint, Tableau) have a ready-made contract to build `plan()` and `harvest()` on, matching the precedent set by `spec/archive/kan-82-secret-pii-scanner-redaction` (scanner module built ahead of the harvesters that will call it).

## What changes
- Add `harvesters/framework/plan.py`: a `HarvestPlan` dataclass (`include`, `exclude` glob patterns, `size_cap_bytes`, `budgets`) and a `Budgets` dataclass (`max_files`, `max_bytes`, `max_seconds`, `max_tokens`), each dimension optional/unlimited. `HarvestPlan.is_included(path)` applies exclude-wins-over-include glob matching, per `docs/HARVESTERS.md` rule 5.
- Add `harvesters/framework/budget.py`: a `BudgetTracker` that raises `BudgetExceeded(budget_name)` the moment the next object would push files, bytes, time or tokens over a budget, and a `run_with_budget(objects, budgets, process)` helper that iterates objects, catches `BudgetExceeded`, and returns `(RunStatus.PARTIAL, usage, budget_name)` instead of letting the run error out — i.e. it stops cleanly and names what was hit. Completing without hitting a budget returns `RunStatus.COMPLETED`.
- Unit tests for both modules: include/exclude precedence, default (unlimited) plan, a plan holding all four budget dimensions, and one test per budget dimension (files, bytes, tokens, time) proving the run stops cleanly, is marked `PARTIAL`, and names the exceeded budget, plus a completed-run case.
- Wire the new `harvesters` package into CI (`ruff check` and the `test-python` matrix) and `pyproject.toml`'s ruff `include`, matching the other Python packages.

## In scope
- The plan model and budget tracker (pure, no I/O, no cloud SDK, no LLM, no source-specific logic).
- Tests with synthetic objects/clocks (no real source, no live harvester).
- CI wiring for the new package.

## Out of scope
- Any actual harvester (`connect`/`discover`/`profile`/`harvest`/`normalize`/`validate`) — Epic 3 (Git harvester) and later source types are not built yet; this module is the shared contract they will import.
- The `harvest_runs` table / run-state persistence, the `ValidationReport`, or the `PARTIAL` run state being written to Postgres — no `harvest_runs` table exists yet (that is scheduler/Epic 4 scope); `RunStatus` here is an in-memory enum returned to the caller, not a persisted state machine.
- Size-cap enforcement at fetch time (per-object skip-if-too-large) — `size_cap_bytes` is carried on the plan for a future harvester to use; this story's budgets are the four run-level dimensions named in the AC (files, bytes, time, tokens).
- LLM-assisted plan generation from a profile (`docs/HARVESTERS.md` section 6) — out of scope; this is the plan data model and enforcement only.
- A schema migration — nothing here is persisted to Postgres.

## Acceptance criteria (from Jira)
1. Plan holds include/exclude rules, caps and budgets (files, bytes, time, tokens) -> scenarios: plan-holds-caps-and-budgets, include-exclude-precedence, default-plan
2. Run stops cleanly and is marked PARTIAL when a budget is hit -> scenarios: budget-hit (files/bytes/tokens/time), run-completes-without-budget-hit

## Affected
Capabilities: spec/capabilities/harvester-framework.md (adds a "Harvest plan model" requirement; the existing "Budgets" requirement already describes this behavior and is unchanged)   Docs/contracts: none (no schema/ontology/harvester-interface change; `docs/HARVESTERS.md` already documents the `plan()` step and budget rule this implements)

## Risks and open questions
- No `harvesters/` package exists yet, so there is no real call site today beyond the tests; future Git-harvester work (Epic 3) should import `harvesters.framework.plan.HarvestPlan` and `harvesters.framework.budget.run_with_budget` when it lands, per `docs/HARVESTERS.md`.
- `RunStatus` is returned to the caller in-memory only; when `harvest_runs` (Epic 4) is built, the caller is expected to persist `PARTIAL`/`COMPLETED` there — not this story's scope.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
