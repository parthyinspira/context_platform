---
name: start-story
description: Start work on a Jira story (KAN-n). Use at the beginning of every story to load the acceptance criteria and project rules, create the branch and agree a plan before writing code.
---

# Start a story

Input: a Jira key such as `KAN-101`.

1. Read the story (summary, description, acceptance criteria, parent epic) with the Atlassian connector. If it cannot be read, ask the user to paste it. Do not guess the acceptance criteria.
2. Read `CLAUDE.md`. Then read the docs that apply to this story:
   - harvester work: `docs/HARVESTERS.md`
   - architecture, adapters, MCP: `docs/ARCHITECTURE.md`
   - UI work: `docs/UI_DESIGN.md`
   - agent work: `docs/DEMO_AGENTS.md`
   - scope questions: `docs/HACKATHON_SCOPE.md`
3. Check scope: is the story in scope per `docs/HACKATHON_SCOPE.md`? Does it contradict a contract in `CLAUDE.md`? If so, stop and tell the user.
4. Create branch `kan-<n>-short-slug` from the latest `main`.
5. Write a short plan: files to add or change, tests to write, contracts or docs that will change, and how each acceptance criterion will be shown. Keep the change small (one PR, under about 400 changed lines); propose splitting the story if it is larger.
6. Show the plan and wait for approval before implementing.

Rules while implementing: only the story's scope; no cloud SDK imports outside `adapters/`; no secrets in code or fixtures; schema changes only through migrations; tests with the code.
