---
name: spec-batch
description: Build a whole milestone (a set of Jira stories) with one combined plan approval, then develop, verify and PR them in order. Use when the user wants to build many stories quickly (for example "build M1").
---

Follow `spec/workflow/06-batch.md` and `docs/MILESTONES.md`. Input: a bundle name from `docs/MILESTONES.md` (B0 to B12) or an explicit list of KAN keys. If both are given, use the explicit list.

1. `git pull origin main`; create branch `m<n>-<slug>` from latest `main`. Check prerequisites listed for the milestone (Docker running, `.env` present, Python available); if missing, stop and say what to do.
2. Plan all stories without stopping: for each KAN key read the story (never guess acceptance criteria), then create `spec/changes/kan-<n>-<slug>/` with proposal, spec delta and tasks (follow `spec-plan`). Order stories by dependency.
3. Write `spec/changes/_batch/<milestone>.md`: a table with story, scope in one line, scenarios count, task count, risks, open questions. Run `python scripts/spec_check.py <folder>` on each change (the missing "Approved by" is expected).
4. Stop once and ask the user to approve the whole batch. When approved, record "Approved by: <name>, <date>" in every proposal and re-run `spec_check`.
5. Build in order. For each story: tests first, then code (follow `spec-develop`), then `spec-verify` (write `verification.md`). Commit per story with `KAN-<n>:` messages. Do not stop between stories unless a stop condition in `06-batch.md` applies.
6. After all stories: run the `contract-check` and `secret-scan` skills, run the milestone check from `docs/MILESTONES.md` (for example `docker compose up` and call the health and API endpoints), and record results in the batch summary.
7. Run the `story-reviewer` agent on the whole branch in a fresh context; fix `[blocking]` findings (two rounds maximum).
8. Push the branch and open one PR titled `<milestone>: <name>` using the PR template. Do not merge. Give the user a short report: what works, how to run it, what is not verified.

Never push to `main`, merge, or skip a failing check.
