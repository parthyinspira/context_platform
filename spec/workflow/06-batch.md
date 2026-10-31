# Batch mode (milestones)

Batch mode keeps the five stages and the gates but moves the human approval from "per story" to "per milestone", so building does not stall on many small approvals.

## What stays
- Every story still has its own change folder, spec deltas, tasks and `verification.md`.
- Tests first, `spec_check` on every change, contract check, secret scan.
- The reviewer agent still runs, on the whole milestone branch.
- The human still approves plans (once, together) and merges (once, at the end). Nothing is merged or pushed to `main` by an agent.

## What changes
1. One combined plan review: the agent creates all change folders and a summary table (`spec/changes/_batch/<milestone>.md`); you approve once.
2. Stories are built in dependency order without stopping between them.
3. One PR per milestone, one commit group per story (`KAN-n: ...`).

## Stop conditions (the agent must stop and ask)
- A scenario or test cannot be made to pass after two fix attempts.
- A story needs something outside its approved proposal, or a contract change (schema, ontology, interface) not in the plan.
- Missing input: credentials, Docker not running, an LLM key, an unclear requirement.
- `contract-check`, `secret-scan` or `spec_check` fails and cannot be fixed within scope.
- A destructive or outward-facing action is needed (push to `main`, deleting data, deploying).

## End of milestone
Run the milestone's "You can then" check from `docs/MILESTONES.md` (for example `docker compose up` and open the UI), record the result in the batch summary, run `story-reviewer` on the branch, then open one PR.

## Auto mode for one story (`spec-auto`)
For a single story, `spec-auto` runs plan, develop, verify, PR and review in one go. The human gate moves from "approve the plan" to "review the PR and the reviewer's verdict". Starting `spec-auto` is the explicit pre-approval; `proposal.md` records "Approved by: auto (user started spec-auto), <date>; human review at PR". Everything else is unchanged: tests first, `spec_check`, `contract-check`, `secret-scan`, the reviewer agent, the stop conditions above, and no merge or push to `main` by an agent. Use it for well-specified stories; use the normal five stages when the story is risky or unclear.
