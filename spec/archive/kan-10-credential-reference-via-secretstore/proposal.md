# KAN-10: Credential reference via SecretStore

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-10   Epic: KAN-2 Source registry/API   Branch: kepler/kan-10-credential-reference-via-secretstore

## Why
`POST /sources` (KAN-7) already stores only `credentials_ref` — a reference key — and never a secret value; that story explicitly deferred "resolving `credentials_ref` through `SecretStore`" to a later story, since that happens when a harvester runs, not at registration. No harvester exists yet (Epic 3), but the resolution mechanism harvesters will depend on does not exist either: there is no code path that turns a `credentials_ref` string into an actual secret value via the `SecretStore` interface, and there is no explicit guard proving the API surface never logs or returns a resolved value. This story closes that gap: add the resolution function harvesters will call, and lock in (with tests) that the API layer never stores, logs or returns a secret value — only the reference key.

## What changes
- Add `adapters/secret_store/resolve.py` with `resolve_credential(credentials_ref: str, secret_store: SecretStore) -> str`, the one function any future harvester uses to turn a `sources.credentials_ref` key into the actual secret (via `EnvSecretStore` locally, Docker secrets by the same `env` adapter). Raises a clear, non-secret-containing error (`CredentialNotFoundError`, carrying only the `credentials_ref` key, never a value) when the key does not resolve, so a misconfigured source fails loudly instead of silently harvesting with no credential.
- Add a contract/unit test proving `resolve_credential` never appears in any log message and that its exceptions never include the secret value (only the key).
- Add a regression test on the `POST /sources` / response path proving that even when the `credentials_ref` matches a real environment variable (i.e. a real secret is resolvable), the request/response cycle and captured logs never contain that secret's value — only the reference key — formalizing the guarantee the API has had since KAN-7.
- Update `spec/capabilities/source-registry.md`: make the existing "Credentials are references" requirement explicit that resolution happens only through `SecretStore.get`, via the new `resolve_credential` helper, and add the "resolve via SecretStore" and "unknown credentials_ref" scenarios.

## In scope
- `adapters/secret_store/resolve.py`: `resolve_credential` + `CredentialNotFoundError`.
- Tests: resolve success, resolve missing key (error carries no value), no-logging guarantee, API-layer non-leakage regression test.
- `spec/capabilities/source-registry.md` delta (new scenarios under the existing "Credentials are references" requirement).

## Out of scope
- Any harvester implementation (Epic 3) — this only adds the resolution function harvesters will later import from `adapters.secret_store.resolve`.
- New SecretStore backends (Secret Manager / Key Vault adapters) — still `env`-only per CLAUDE.md's "env/Docker secrets locally" default; cloud adapters are a separate story per the adapter interface pattern.
- Any new API route (`GET /sources`, credential-test endpoints, etc.) — not named in the AC.
- Changes to the `sources` table schema — `credentials_ref` already exists (KAN-4).

## Acceptance criteria (from Jira)
"credentials_ref is a key resolved by SecretStore (env/Docker secrets locally); API never stores, logs or returns secret values."
1. credentials_ref is a key resolved by SecretStore -> scenarios: resolve-credential-success, resolve-credential-missing-key
2. API never stores, logs or returns secret values -> scenarios: register-a-source (existing), api-never-logs-resolved-secret (new)

## Affected
Capabilities: `spec/capabilities/source-registry.md` (extends "Credentials are references" requirement with explicit resolution scenarios)   Docs/contracts: none (no schema/ontology/harvester-interface change; Confluence Contracts page unaffected)

## Risks and open questions
- No harvester exists yet to consume `resolve_credential` end-to-end; this story proves the function and its non-leakage guarantees in isolation (unit/contract tests) rather than a full harvester integration, consistent with the build order (Epic 3 comes after Epic 2).
- `CredentialNotFoundError` is a new exception type in `adapters/secret_store/`; kept minimal (message carries only the `credentials_ref` key) to avoid scope creep into retry/alerting behavior, which is not named in the AC.

## Changes during development
(none)

## Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
