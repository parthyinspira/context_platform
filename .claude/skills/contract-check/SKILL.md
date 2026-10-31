---
name: contract-check
description: Check that code, docs and contracts agree. Use before opening a PR, and whenever a change touches the schema, ontology, harvester interface, adapters or MCP tools.
---

# Contract check

Compare the change (`git diff origin/main...HEAD`) against the contracts. Report each mismatch with file and line.

1. **Schema:** any table or column change must have a migration, and match "Postgres schema" in `CLAUDE.md` and the Confluence Contracts page. Flag schema edits without a migration.
2. **Ontology:** entity and relation types in code must match "Ontology v0" in `CLAUDE.md`. New types must go through `proposed_changes`, not be added silently.
3. **Harvester interface:** implementations must provide connect, discover, profile, plan, harvest, normalize and validate per `docs/HARVESTERS.md`. Check budgets, size caps, manifest recording and a validator test.
4. **Adapters:** search for cloud SDK imports (`google.cloud`, `azure`, `boto3`) outside `adapters/`; business logic must use `EventBus`, `ObjectStore`, `SecretStore`, `LLMProvider`, `EmbeddingProvider`.
5. **MCP tools:** names, inputs and outputs must match `docs/ARCHITECTURE.md`; every result carries source link, `harvested_at` and `sensitivity`.
6. **Secrets:** search the diff and fixtures for keys, tokens and passwords; confirm `.env` is untracked.
7. **Docs:** if a contract changed, `CLAUDE.md`, the relevant `docs/*.md` and the Confluence Contracts page must be updated in the same PR. If a doc is wrong, fix the doc or the code, not neither.

Output: a list of mismatches (or "no mismatches"), and for each the fix needed. Do not change contracts silently; if the code is right and the contract is wrong, say so and ask the user.
