# Design

## Context
The scheduler container is a health-only stub. KAN-106 needs it to accept a run request and expose due sources, without building the full harvest-runs lifecycle (later epic) or Airflow.

## Options considered
1. **Minimal `dispatcher_runs` table, no harvester launch (chosen).** Matches B2 "Sources API" scope per `docs/MILESTONES.md`; defers the real lifecycle table and container launch to B4.
2. **Build `harvest_runs` now with full lifecycle states.** Rejected: that table and its states are explicitly scoped to KAN-75+ (B4 Harvest core); building it here would duplicate/conflict with that story's design.
3. **Hand-roll cron "due" math instead of a dependency.** Rejected: `schedule` is already a full 5-field cron expression (validated in `api/app/schemas.py`); a hand-rolled parser would either be incomplete or duplicate `croniter`. Added `croniter` (pure Python, no cloud SDK) instead.

## Decision and reason
Add `dispatcher_runs` (provisional) + two scheduler endpoints, reusing the existing `EventBus`/`SecretStore` adapters and the `api/app/main.py` dependency-injection pattern. This keeps the dispatcher inside its own container boundary (per `docs/ARCHITECTURE.md`'s adapter table: "Scheduling | dispatcher | compose scheduler | ...") and avoids Airflow entirely.

## Consequences
- `dispatcher_runs` will likely be replaced or merged into `harvest_runs` once B4 lands; flagged in `proposal.md` risks.
- The scheduler's Docker build context changes to the repo root (like `api`) so it can `COPY adapters`.
