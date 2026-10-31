---
name: spec-auto
description: Run one Jira story end to end in a single step: plan, develop, verify, open the PR and run the reviewer. Use only when the user explicitly starts it; starting it counts as pre-approval of the plan.
---

Follow `spec/workflow/06-batch.md` (section "Auto mode for one story"). Input: a Jira key (or the story attached to the task).

1. Read the story (never guess acceptance criteria), `CLAUDE.md`, matching `spec/capabilities/*.md` and `docs/`. Check scope against `docs/HACKATHON_SCOPE.md`. Make sure the branch exists (`kan-<n>-<slug>`) from latest `main`.
2. Plan (`spec-plan` steps) without stopping: proposal, spec deltas, tasks. In `proposal.md` write "Approved by: auto (user started spec-auto), <date>; human review at PR". Run `python scripts/spec_check.py <change-folder>`.
3. Develop (`spec-develop`): tests first, stay inside the proposal.
4. Verify (`spec-verify`): `verification.md` with evidence; run `contract-check` and `secret-scan`; run `spec_check --stage=verify`.
5. Open the PR (`spec-pr`) using the PR template, with the plan summary and any "not verified" items called out near the top.
6. Run the `story-reviewer` agent in a fresh context on the branch. Fix `[blocking]` findings (two rounds maximum), re-verify, push the fixes.
7. Report: what was built, evidence per acceptance criterion, reviewer verdict, anything not verified, and what you need to decide.

Stop and ask only for the stop conditions in `06-batch.md` (missing input, scope or contract change outside the story, failing checks after two attempts, outward-facing actions). Never merge, and never push to `main`.
