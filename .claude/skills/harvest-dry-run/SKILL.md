---
name: harvest-dry-run
description: Run a harvester against fixtures or a chosen source without publishing, and print the plan, manifest summary and validator report. Use to tune stack rules and budgets.
---

1. Choose the source (default: fixtures under `fixtures/`). Use read-only credentials; never a production source without the user's explicit say-so.
2. Run connect, discover, profile and plan; print the scope tree, profile (sizes, counts, detected stacks) and the plan (included and skipped by type and bytes, estimates versus budgets).
3. Run harvest into a scratch store (not the published knowledge) and print the manifest summary: fetched, skipped (with reasons), failed.
4. Run the validator and print the report per check.
5. Highlight surprises: large skipped sets, near-budget values, zero-yield types, secrets detected.
6. Suggest rule changes as a diff for the user to approve; do not change rules automatically.
