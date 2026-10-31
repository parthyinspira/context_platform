---
name: spec-plan
description: Stage 1 of spec-driven development. Use at the start of every Jira story (KAN-n) to create the change folder with proposal, spec deltas and tasks, and get the plan approved before any code.
---

Follow `spec/workflow/01-plan.md` exactly. Input: a Jira key.

Produce in `spec/changes/kan-<n>-<slug>/`: `proposal.md`, `tasks.md`, `specs/<capability>.md` deltas, and `design.md` only if there is a real decision. Use the templates in `spec/templates/`. Read the story from Jira (never guess acceptance criteria), `CLAUDE.md`, matching `spec/capabilities/*.md` and `docs/`. Create branch `kan-<n>-<slug>` from latest `main`.

Run `python scripts/spec_check.py <change-folder>`. Show the plan to the user and wait for approval; then record "Approved by" in `proposal.md`. Write no code in this stage.
