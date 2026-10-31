# Stage 5: PR review

**Purpose:** independent check that code matches the spec and the rules.
**Who:** `story-reviewer` agent in a fresh context, then the user. **Inputs:** PR, change folder.

## Review checks
1. **Traceability:** every ADDED/MODIFIED requirement is implemented and has a test; every task is done; nothing in the diff lacks a requirement (flag undocumented behaviour).
2. **Acceptance criteria:** each criterion met, with evidence in `verification.md`. Re-run the tests yourself; do not trust the description.
3. **Scope:** only what the proposal says; no drive-by changes.
4. **Contracts:** schema, ontology, interface, MCP tools match `CLAUDE.md` and `docs/`; changes are documented.
5. **Harvester rules** (if applicable): budgets, size caps, denylists, read-only access, secret redaction, manifest, validator test.
6. **Security basics:** no secrets, no broad permissions, inputs validated. Access-model or credential questions go to the Inspira security team at security@inspirafinancial.com.
7. **Portability and quality:** only `adapters/` touch cloud services; tests meaningful and cover failure paths; UI matches tokens and states.

## Output
Verdict `APPROVE`, `APPROVE WITH NITS` or `CHANGES REQUESTED`; requirement-by-requirement table; findings tagged `[blocking]` or `[nit]` with `file:line` and a fix; what could not be verified.

## Loop
Dev agent fixes blocking findings and updates the spec if needed; reviewer re-checks. Maximum two rounds, then escalate to the user.

## After approval (user merges)
Run `spec-archive`: apply the deltas to `spec/capabilities/`, move the change folder to `spec/archive/`, update docs and Confluence if a contract changed, move the Jira story to Done with the PR link.
