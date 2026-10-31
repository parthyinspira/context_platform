# Development workflow: developer agent plus reviewer agent per story

Every Jira story (`KAN-n`) is built by a **dev agent** and checked by a separate **review agent** before a human merges. The reviewer has no memory of the build session, so it checks the work against the story, not against the developer's reasoning.

## Spec-driven stages (see `spec/README.md`)
| Stage | Skill | Output | Gate |
|---|---|---|---|
| 1 Plan | `spec-plan` | proposal, spec deltas, tasks | you approve |
| 2 Develop | `spec-develop` | tested code, ticked tasks | all tasks done |
| 3 Verify | `spec-verify` | `verification.md` | Status PASS |
| 4 PR | `spec-pr` | pull request | CI green |
| 5 PR review | `spec-review` (agent `story-reviewer`) | verdict | `APPROVE`, then you merge |
| After merge | `spec-archive` | specs updated, change archived | story Done |

Supporting skills:
- Build helpers: `new-migration`, `new-adapter`, `new-mcp-tool`, `new-harvester`, `ui-screen`
- Quality and safety: `contract-check`, `secret-scan`, `eval-run`, `harvest-dry-run`
- Data and ops: `demo-data`, `triage-failed-run`, `confluence-sync`, `demo-check` Mechanical guards as code appears: `scripts/spec_check.py` in CI, lint and tests, an import rule blocking cloud SDKs outside `adapters/`, migrations-only schema changes, secret scanning.

## Steps
1. **Pick** a story; read its acceptance criteria and the relevant docs (`CLAUDE.md`, `docs/HARVESTERS.md`, `docs/ARCHITECTURE.md`, Confluence Contracts).
2. **Dev agent** (Claude Code session): creates branch `kan-<n>-slug`, plans, implements with tests, runs lint and tests, updates docs and contracts if they changed, opens a PR whose description follows `.github/pull_request_template.md`.
3. **Review agent** (`story-reviewer`, read-only, fresh context): reads the story, the diff and the docs; writes a review with blocking and non-blocking findings.
4. **Dev agent** fixes blocking findings; the reviewer re-checks. Maximum two rounds, then escalate to the human.
5. **Human** reviews the summary plus the reviewer's verdict, then merges.
6. Jira: move to In Review at PR open, Done at merge, with a comment linking the PR.

## Definition of done
- Every acceptance criterion is met and demonstrable (test or screenshot).
- Tests added and passing; lint clean; runs from `docker compose up`.
- Contracts and docs updated in the same PR (schema, ontology, harvester interface, Confluence note).
- Harvester work follows the budgets and metadata-first rules and ships a validator test.
- No secrets in code, logs or fixtures; no direct cloud SDK imports outside `adapters/`.
- Reviewer verdict is `APPROVE`.

## Reviewer checklist (the agent follows this)
1. **Scope:** does the diff do what the story says, and only that?
2. **Acceptance criteria:** each one mapped to evidence.
3. **Correctness:** edge cases, idempotency, error handling, incremental behaviour.
4. **Contracts:** schema, ontology and interface changes are intentional and documented.
5. **Harvester rules** (if applicable): budgets, size caps, denylists, read-only access, secret redaction, manifest and validator coverage.
6. **Tests:** meaningful, include failure paths; fixtures are non-sensitive.
7. **Security basics:** no secrets, no overly broad permissions, inputs validated. Questions about access models or credential handling go to the Inspira security team at security@inspirafinancial.com.
8. **Portability:** only `adapters/` touch cloud services.
9. **UI work:** matches `docs/UI_DESIGN.md` tokens and components; states (empty, loading, error) present; accessibility basics.

Verdict format: `APPROVE`, `APPROVE WITH NITS`, or `CHANGES REQUESTED`, with findings tagged `[blocking]` or `[nit]` and a file:line reference.

## Tips for running it
- Run the reviewer as a **subagent or a separate session** so it does not inherit the developer's assumptions.
- Keep stories small (one PR, under about 400 changed lines) so reviews stay sharp.
- Have the reviewer run the tests itself rather than trusting the PR description.

## Using Kepler (or any launcher) with these guidelines
Kepler should run Claude Code with the working directory set to a clone of this repo, so it loads `CLAUDE.md`, `.claude/skills/` and `.claude/agents/` automatically. Checklist:
1. The repo clone (or worktree) Kepler uses contains `.claude/` (it is committed on `main`; branch from latest `main`).
2. Kepler's Plan prompt (if configurable) says: "Work on {ticket}. Follow CLAUDE.md. Start with the spec-plan skill and wait for my approval before writing code."
3. Smoke test: in a Kepler session ask "List this project's skills and the first rule in CLAUDE.md's entry rules." If it cannot, Kepler is not running in the repo.
4. Keep Kepler's permissions so it can read Jira and run tests, but require confirmation for `git push` and anything that merges.
