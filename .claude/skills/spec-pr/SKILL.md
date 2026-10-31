---
name: spec-pr
description: Stage 4 of spec-driven development. Use after verification passes to open a small, well-described pull request linked to the change folder.
---

Follow `spec/workflow/04-pr.md`. Require `verification.md` Status PASS. Rebase on `main`, then open the PR titled `KAN-<n>: <summary>` using `.github/pull_request_template.md`, filled with the change folder link, acceptance criteria with evidence, and docs updated. Check size (about 400 changed lines). Wait for CI; fix failures before requesting review. Move the Jira story to In Review with a comment linking the PR.
