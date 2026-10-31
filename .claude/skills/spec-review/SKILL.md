---
name: spec-review
description: Stage 5 of spec-driven development. Use to review a PR against its change folder by running the story-reviewer agent in a fresh context.
---

Follow `spec/workflow/05-pr-review.md`. Launch the `story-reviewer` agent on the branch or PR; give it only the PR and the change folder path, not your own reasoning. Relay its verdict and findings. For `CHANGES REQUESTED`, fix the `[blocking]` findings (update the spec delta if behaviour changes) and re-run the reviewer, at most two rounds, then escalate to the user. Never merge; the user merges.
