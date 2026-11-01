# KAN-64: Run view with stage timeline and budget meters (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-64   Branch: m8-ui-wizard-and-runs

## Scope
In: rewire `RunView.jsx` to poll `GET /runs/{id}` (KAN-58) and render the existing `Timeline` (stage progress) and `Meter` (files/bytes/time/tokens budgets) components, a simple log view listing manifest entries as lines, a "Stop" button calling `PATCH /runs/{id}/stop`, and a final-state panel (PUBLISHED/QUARANTINED/FAILED/PARTIAL) with next-step links (to the validation report for KAN-65, or back to Sources).
Out: a real push/streaming transport (polling only, per KAN-58's scope decision); true container cancellation (Stop marks the run FAILED via the API; it does not kill a running harvester process, which this codebase has no mechanism for — documented as a known limitation).

## Acceptance criteria (from Jira)
1. Live stage and counts.
2. Log stream.
3. Meters for files/bytes/time/tokens.
4. Stop button.
5. Final state with next steps.

## Requirements (at most 5)
- `RunView` SHALL poll `GET /runs/{id}` on an interval while the run is non-terminal and render a `Timeline` whose stages map from `HarvestRunState` (Connecting/Discovering/Profiling/Harvesting/Validating/Published or Quarantined/Failed), with counts from the manifest summary shown alongside. (scenario: Given a run in state HARVESTING with manifest counts, When RunView renders, Then the Timeline shows Harvesting as active and the counts are shown; Given the run reaches PUBLISHED, Then polling stops and Published is marked done)
- `RunView` SHALL render a scrollable log list, one line per manifest entry (`ref`, `outcome`, `outcome_reason`), newest last. (scenario: Given a manifest with three entries, When rendered, Then three log lines are shown in entry order)
- `RunView` SHALL render a `Meter` for each of files/bytes/time/tokens using the run's plan budgets as `max` and the manifest's current counts as `value`, when a budget is set; a budget left unset (`null`) SHALL render that `Meter` in its `empty` state. (scenario: Given a plan with `max_files` set and a manifest with a fetched count, When rendered, Then a files Meter shows value/max; Given `max_tokens` is null, Then the tokens Meter renders empty)
- A "Stop" button, visible only while the run is non-terminal, SHALL call `PATCH /runs/{id}/stop` and reflect the resulting terminal state. (scenario: Given a run in state HARVESTING, When Stop is activated and the API succeeds, Then the view shows the run as Failed with "stopped by user"; Given the run is already terminal, Then no Stop button is shown)
- Once a run reaches a terminal state, `RunView` SHALL show that state and a next-step action: a link to the validation report (KAN-65) for PUBLISHED/QUARANTINED/PARTIAL, or back to Sources for FAILED. (scenario: Given state PUBLISHED, When rendered, Then a "View validation report" link is shown; Given state FAILED, Then a "Back to sources" action is shown instead)

## Tasks
- [x] 1. `ui/src/api.js`: add `getRun(runId)` and `stopRun(runId)` (tests: resolve with run shape / success)
- [x] 2. Rewrite `RunView.jsx` to poll and render `Timeline` + log list (tests: stage mapping, log lines, polling stops at terminal state)
- [x] 3. Add `Meter`s for the four budgets, including the `empty` case for an unset budget (test: value/max rendering + empty case)
- [x] 4. Stop button wiring (tests: visible while non-terminal, calls stopRun, hidden once terminal)
- [x] 5. Terminal-state next-step panel (tests: published→report link, failed→back-to-sources)
- [x] 6. Extend KAN-58's `GET /runs/{id}` response with `manifest_summary.fetched_bytes` and a `log_entries` list (small additive fields the run-view genuinely needs; `api/app/schemas_runs.py`, `api/app/routes_runs.py`)

## Risks / not verifiable here
- Stop is a best-effort API state change (`FAILED`, error "stopped by user"); this codebase has no job-control mechanism to actually interrupt a running harvester container, so "stopping" a real in-flight `docker compose run harvester` process is out of scope here (tracked as a pre-existing gap, not introduced by this story).
- The files and bytes Meters have real live values (`manifest_summary.fetched`/`fetched_bytes`, the latter added in task 6); the time/tokens Meters show `0` against their budget when a budget is set, because the harvester runner does not track live elapsed-time or token usage anywhere yet (a bigger change to `harvesters/run.py`'s execution loop, out of scope for a UI story). Documented rather than fabricated.

## Approval
Approved by: parthasarathy.venkatachalam (user approved spec-batch), 2026-10-31
