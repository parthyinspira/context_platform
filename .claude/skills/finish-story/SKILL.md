---
name: finish-story
description: Finish a Jira story. Use when implementation is done to run checks, update docs and contracts, open the PR from the template and run the story-reviewer agent before asking for a merge.
---

# Finish a story

1. Run lint and the full test suite. Fix failures; never skip or weaken a test to pass.
2. Run the `contract-check` skill. Resolve every mismatch it reports.
3. Check the Definition of Done in `docs/DEV_WORKFLOW.md`:
   - every acceptance criterion has evidence (a test name or a screenshot)
   - works from `docker compose up`
   - no secrets; cloud SDKs only in `adapters/`
   - harvester work follows `docs/HARVESTERS.md` (budgets, metadata first, validator test)
   - UI work follows `docs/UI_DESIGN.md` (tokens, empty/loading/error states)
4. Commit with a message that starts with the story key. Push the branch.
5. Open the PR with `.github/pull_request_template.md`, filling in every section with real evidence. Put the story key in the title.
6. Run the `story-reviewer` agent on the branch in a fresh context. Fix every `[blocking]` finding; re-run the reviewer at most twice. If a blocking finding remains after two rounds, stop and tell the user.
7. Summarise for the user: what changed, evidence per acceptance criterion, reviewer verdict, anything not verified.
8. Do not merge. After the user merges, move the Jira story to Done with a comment linking the PR.
