---
name: spec-develop
description: Stage 2 of spec-driven development. Use after the plan is approved to implement the tasks test-first, keeping to the proposal's scope.
---

Follow `spec/workflow/02-develop.md`. Refuse to start if `proposal.md` has no approval.

Work through `tasks.md` in order: test for the scenario first, then code, then tick the task. Commit per task group with messages starting `KAN-<n>:`. Respect project rules (no cloud SDKs outside `adapters/`, migrations only, no secrets, harvester rules in `docs/HARVESTERS.md`, UI rules in `docs/UI_DESIGN.md`). If behaviour changes, edit the spec delta in the same commit. If work falls outside the proposal, stop and ask; never expand scope silently.
