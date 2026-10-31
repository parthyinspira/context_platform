# M8: UI wizard and runs — batch plan

Branch: `m8-ui-wizard-and-runs`   Base: `main` (1fefb23)

| Story | Scope (one line) | Scenarios | Tasks | Risks | Open questions |
|---|---|---|---|---|---|
| KAN-58 | New `api/` routes: test-connection, discover, plan preview, run create/read/stop, validation report, graph query, over existing `harvest_runs`/entities/edges | 11 | 7 | `Harvester.validate()` contract has no counts/samples field; git harvester `normalize`/`validate` still `NotImplementedError` (pre-existing) | None blocking — both risks are pre-existing gaps outside this story's scope |
| KAN-61 | Wizard steps 1-2: type tiles (Git only enabled), connect form, Test connection, masked secrets | 7 | 4 | Only Git has a real credential form; others are visibly disabled, matching AC's intent | None |
| KAN-62 | Wizard step 3: `ScopeTree` wired to discover, checkbox selection w/ parent/child propagation, search, select-recommended | 8 | 4 | "Recommended" = select-all leaves (no scoring signal exists upstream) | None |
| KAN-63 | Wizard steps 4-5: `PlanSummaryCard` (pulled/skipped, estimates, budget warnings), editable include/exclude list, Run now | 9 | 4 | None beyond KAN-58's | None |
| KAN-64 | `RunView` rewrite: polling `Timeline`, log list, 4 budget `Meter`s, Stop button, terminal-state next steps | 10 | 5 | Stop is a best-effort state change, not real process cancellation (no job-control mechanism exists) | None |
| KAN-65 | New `ValidationReport` screen: status `Badge`, per-check counts/samples, quarantine explanation, 404 fallback | 7 | 4 | Real counts/samples depend on a future story populating `harvest_runs.report` from a richer `validate()`; verified here against seeded data | None |

**Total**: 6 stories, 52 scenarios, 28 tasks.

**Dependency order for build**: KAN-58 (backend, everything else depends on it) → KAN-61 → KAN-62 → KAN-63 → KAN-64 → KAN-65.

**Cross-story design decisions** (made once, applied everywhere above):
- Run status is polling-based (`GET /runs/{id}` on an interval), not SSE/websocket — simplest thing that satisfies "run status stream" for a hackathon UI; documented in KAN-58/KAN-64 plans.
- A new nullable `harvest_runs.report JSONB` column (one small migration) backs KAN-65's validation report; it will be NULL for any run driven by today's harvesters (their `validate()` doesn't return per-check counts/samples), which both KAN-58 and KAN-65 call out explicitly as a pre-existing, out-of-scope gap rather than hiding it.
- Stop (KAN-64) sets state `FAILED` via the API; it does not cancel a running container process (no such mechanism exists in this codebase).
- "list/create sources" (part of KAN-58's AC) is already implemented from bundle B2 (KAN-7/8/9/10) — KAN-58 only documents/reuses it, no new code.

Run `python scripts/spec_check.py spec/changes/kan-<n>-...` on each change folder below (missing "Approved by" expected pre-approval).
