# Lite mode (default for the remaining work)

Purpose: keep the process, cut the paperwork and repeated token cost. Use lite mode for ordinary stories; use the full five stages for risky or unclear ones.

## Artifacts
- One `plan.md` per story (`spec/templates/plan-lite.md`): scope, acceptance criteria, at most 5 requirements, task checklist, risks, approval. No separate `design.md` unless there is a real decision (put it in plan.md).
- One short `verification.md` (`spec/templates/verification-lite.md`): one row per acceptance criterion.
- `scripts/spec_check.py` detects lite mode (plan.md present, no proposal.md) and checks plan.md and verification.md.

## Where the cost is cut
1. Per story: tests and `secret-scan` only; at most 3 tests per requirement; no Docker run.
2. Per bundle (once, at the end): `docker compose up` and health checks, `contract-check`, the bundle's "done when" check, and ONE `story-reviewer` run on the whole branch (review the diff; do not re-run all tests, CI does that).
3. Archive once per bundle (`spec-archive` over all the bundle's change folders), not after every story.
4. Read only what the story needs: use the docs index in `CLAUDE.md`; read one section, not whole files.
5. Take acceptance criteria from the task description if present; only call Jira when they are missing.
6. Minimal means minimal: implement the acceptance criteria and nothing else.

## What does not change
Tests first, `spec_check`, secret scan, no secrets in code, no cloud SDKs outside `adapters/`, migrations only, no merge or push to `main` by an agent, the stop conditions in `06-batch.md`, and human review of the PR.
