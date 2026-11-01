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

## Build results (all 6 stories complete)

- All 6 `plan.md`/`verification.md` pairs pass `spec_check.py --stage=verify`.
- `python -m pytest api/tests -q` → 43 passed. `npm test` (ui/) → 91 passed.
- `python -m pytest scheduler/tests harvesters harvest_validation -q` (pre-existing, unaffected) → 8 / 127 / 68 passed.

## Bundle-wide checks (run once, per lite mode)

- **contract-check**: one mismatch found and fixed — migration `0005_harvest_runs_report` added a `report JSONB` column to `harvest_runs` that `CLAUDE.md`'s Postgres schema v0 listing didn't mention; `CLAUDE.md` updated in the same branch. No other mismatches (ontology, harvester interface, adapters/cloud-SDK isolation, MCP, secrets all clean for this diff).
- **secret-scan**: no secrets found. Only `.env.example` is tracked; no key/token/password-shaped literals in the diff outside test fixture placeholders (`"super-secret-token"`, `"dummy-token"`) which are deliberately never-real values asserted to never round-trip back to the UI.
- **Docker/milestone check**: `docker compose up postgres migrate api scheduler ui` — all four services reached healthy. Found and fixed a real gap during this check: the `api` image didn't copy the `harvesters/` package or install the `git` CLI, so the container crashed on the new `routes_discovery.py` import chain (`ModuleNotFoundError: No module named 'harvesters'`); fixed in `api/Dockerfile`/`api/requirements.txt` (adds `harvesters/`, the `git` binary, `pyyaml`).
- **Live browser walkthrough** (Playwright, headless Chromium, driving the real containerized stack — not mocks): Sources → Add source → select Git → enter `https://github.com/octocat/Hello-World.git` → Test connection (succeeded against the real GitHub remote) → Add source → scope tree discovered for real (`README`, 13 bytes) → Select recommended → Plan step (real estimates: 13 bytes, 1 file, 3 tokens) → Run now → Run view (timeline, 4 meters, Stop button) → Stop → FAILED state with "Back to sources". Zero browser console errors throughout.
  - Separately verified the validation-report screen end to end by seeding a `PUBLISHED` run with a report via SQL (since no harvester populates that column today — documented gap): the "View validation report" link appeared, and the screen correctly rendered a WARN badge, both checks with their counts/samples, and "none" for the empty-sample check.
  - Not demonstrated live: a harvest actually reaching `PUBLISHED`/`QUARANTINED` through the real pipeline (git harvester `normalize()`/`validate()` are pre-existing `NotImplementedError`s, called out repeatedly above) and the Stop button's effect on a genuinely in-flight container (no job-control mechanism exists).
  - Visual polish: the reused shared components (`Stepper`, `ScopeTree`, `Timeline`, `Meter`, `Badge`) render with full token styling; the new wizard/plan/report chrome (buttons, labels, containers) is functionally correct but unstyled plain HTML — consistent with "minimal: implement only the acceptance criteria, no extras," but worth a follow-up polish pass before the real demo.

## Review (story-reviewer, fresh context, round 1)

Verdict: CHANGES REQUESTED, one blocking finding — fixed, not re-reviewed (lite mode: two rounds max, fix applied directly since it was a single well-scoped, mechanical fix).

- **[blocking, fixed]** Every new route in `routes_discovery.py`/`routes_runs.py`/`routes_graph.py` opened a Postgres connection via `connection_factory()` but never closed it, unlike every pre-existing route in `api/app/main.py` (which all use `try/finally: conn.close()`). Worst exposure: `RunView` polls `GET /runs/{id}` every 2s for the life of any non-terminal run. Fixed with the identical existing pattern; each affected fake-DB test now asserts `conn.closed is True` so a regression would be caught.
- **[nit, fixed]** KAN-64's plan.md/verification.md said the bytes Meter shows a hardcoded `0`; the code actually wires it to the real `manifest_summary.fetched_bytes` (added by the same story's task 6) — docs corrected to match.
- **[nit, fixed]** KAN-62's checkbox-propagation scenario only tested "check all children on parent click", not "uncheck one child unchecks the parent" (the other half of the same requirement's scenario) — test added.
- Confirmed clean by the review: requirement traceability for all 6 stories, scope containment (no story did another's work), the `api/Dockerfile`/`api/requirements.txt` fix, the `CLAUDE.md` schema contract update, no cloud-SDK imports, no secrets, parameterized SQL throughout.
- Full re-run after fixes: `python -m pytest api/tests -q` → 43 passed (now including the `conn.closed` assertions); `npm test` (ui/) → 91 passed.
