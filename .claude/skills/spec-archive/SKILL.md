---
name: spec-archive
description: After a PR is merged, apply the change's spec deltas to spec/capabilities/, move the change folder to spec/archive/, and close the Jira story.
---

Run only after the user confirms the PR is merged. Apply ADDED, MODIFIED and REMOVED requirements from `spec/changes/kan-<n>-<slug>/specs/*.md` to `spec/capabilities/`. Move the change folder to `spec/archive/`. Update `CLAUDE.md`, `docs/` and the Confluence Contracts page if a contract changed. Move the Jira story to Done with a comment linking the PR. Commit on a small follow-up branch and open a PR.
