# Stage 1: Plan

**Purpose:** agree exactly what will change before any code.
**Who:** dev agent proposes; the user approves.
**Inputs:** Jira story (summary, acceptance criteria, parent epic), `CLAUDE.md`, `spec/capabilities/`, relevant `docs/`.

## Steps
1. Read the story with the Atlassian connector; if unavailable ask the user to paste it. Never guess acceptance criteria.
2. Read `CLAUDE.md`, matching `spec/capabilities/*.md`, and the matching docs (`docs/HARVESTERS.md`, `ARCHITECTURE.md`, `UI_DESIGN.md`, `DEMO_AGENTS.md`, `HACKATHON_SCOPE.md`).
3. Check scope against `docs/HACKATHON_SCOPE.md` and the contracts. If the story conflicts, stop and tell the user.
4. Create branch `kan-<n>-<slug>` from latest `main` and folder `spec/changes/kan-<n>-<slug>/`.
5. Write `proposal.md` (template): why, what changes, in scope, out of scope, acceptance criteria copied from Jira, risks, affected capabilities and docs.
6. Write spec deltas in `specs/<capability>.md` using ADDED / MODIFIED / REMOVED requirements with scenarios. Each acceptance criterion maps to at least one scenario.
7. Write `design.md` only if there is a real decision (data model, interface, trade-off); keep it short.
8. Write `tasks.md`: small ordered tasks (each about an hour or less), each tagged with the scenario(s) it satisfies, tests included.
9. Size check: more than about 400 changed lines expected, or more than about 12 tasks, means propose splitting the story.
10. Run `python scripts/spec_check.py spec/changes/kan-<n>-<slug>` and fix errors.

## Exit criteria (gate 1)
- Proposal, deltas and tasks exist and pass `spec_check`.
- Every acceptance criterion maps to a scenario and a task.
- The user has approved the plan in chat. Record "Approved by <name>, <date>" in `proposal.md`.

## Failure handling
Unclear requirement: ask the user. Story too large: split and create the follow-up in Jira. Conflicts with a contract: stop and escalate.
