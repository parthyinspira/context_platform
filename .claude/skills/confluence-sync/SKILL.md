---
name: confluence-sync
description: Sync merged contract changes (schema, ontology, harvester interface, decisions) to the Confluence Project Home and Contracts pages in space SD. Use after spec-archive when a contract changed.
---

1. Identify what changed from the archived change folder and the updated `spec/capabilities/` and `CLAUDE.md` contracts.
2. Read the current Confluence pages first (Project Home and Contracts in space `SD`) with the Atlassian connector. If the connector cannot reach `inspiradataintegration.atlassian.net`, stop and give the user the exact text to paste.
3. Show the user the proposed edits (before and after) and wait for approval before saving. Edit only the affected sections; do not rewrite pages.
4. Add a decision-log row (date, decision, reason) for any architectural decision.
5. Preserve formatting; use the connector's content format guidance for tables and code blocks.
6. Link the PR and Jira story in the change note. Report what was updated.
