# Stage 2: Develop

**Purpose:** implement exactly the approved plan, test-first.
**Who:** dev agent. **Inputs:** approved change folder.

## Steps
1. Work through `tasks.md` in order. Before each task, write the test for its scenario; then the code.
2. Tick the task only when its test passes. Commit per task group; message starts with `KAN-<n>:`.
3. Follow project rules: no cloud SDK imports outside `adapters/`; schema changes only via migrations; no secrets in code, logs or fixtures; harvester work follows `docs/HARVESTERS.md` (budgets, metadata first, manifest, validator test); UI work follows `docs/UI_DESIGN.md` (tokens, empty/loading/error states).
4. Keep the spec current: if behaviour changes during development, edit the delta in the same commit and note it in `proposal.md` under "Changes during development".
5. Scope guard: if a needed change falls outside the proposal, stop. Either add it to the proposal (and ask the user to re-approve) or log a new Jira story. Never silently expand scope.
6. Run lint and the relevant tests locally after each task.

## Exit criteria
- All tasks ticked; all scenario tests exist and pass locally.
- No unrelated changes in the diff.

## Failure handling
Blocked by a missing dependency or an unclear requirement: stop, record the blocker in `tasks.md`, ask the user.
