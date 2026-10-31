# Specs: spec-driven development

Same idea as OpenSpec: **specs are the source of truth, changes are proposed as spec deltas, and code follows the spec.** Every Jira story becomes one change folder that moves through five stages.

```
spec/
  capabilities/      current truth: what the system SHALL do, one file per capability
  changes/           active changes, one folder per story (kan-<n>-<slug>/)
  archive/           finished changes, kept for history
  workflow/          the five stage specs (how we plan, develop, verify, PR, review)
  templates/         templates for change artifacts
```

## The five stages
| # | Stage | Spec | Skill | Output | Gate |
|---|---|---|---|---|---|
| 1 | Plan | `workflow/01-plan.md` | `spec-plan` | `proposal.md`, `tasks.md`, `design.md` (if needed), spec deltas | you approve the plan |
| 2 | Develop | `workflow/02-develop.md` | `spec-develop` | code, tests, ticked tasks | all tasks done |
| 3 | Verify | `workflow/03-verify.md` | `spec-verify` | `verification.md` | status PASS |
| 4 | PR | `workflow/04-pr.md` | `spec-pr` | pull request | CI green |
| 5 | PR review | `workflow/05-pr-review.md` | `spec-review` (agent `story-reviewer`) | review verdict | `APPROVE`, then you merge |

After merge: `spec-archive` applies the deltas to `capabilities/` and moves the change to `archive/`.

## Change folder
```
spec/changes/kan-101-compose-stack/
  proposal.md        why, scope in/out, acceptance criteria from Jira, risks
  design.md          only when there is a real design decision
  tasks.md           small checklist mapped to acceptance criteria
  specs/<capability>.md   deltas: ADDED / MODIFIED / REMOVED requirements
  verification.md    evidence per scenario, written in stage 3
```

## Auto and batch mode
`spec-auto` runs one story end to end in one step (plan, develop, verify, PR, review); the human gate becomes the PR review.
For speed, `spec/workflow/06-batch.md` and the `spec-batch` skill build a whole milestone (`docs/MILESTONES.md`) with one combined plan approval, per-story verification, one reviewer pass and one PR.

## Rules
- No code before the plan is approved. No PR before verification is PASS. No merge before `APPROVE`.
- Requirements use SHALL; every requirement has at least one scenario; every scenario has evidence in `verification.md`.
- If the work needs something outside the proposal's scope, stop and update the proposal; do not drift.
- `scripts/spec_check.py <change-folder>` checks the structure mechanically; CI runs it on PRs.
