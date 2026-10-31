# Verification

Status: PASS
Date: 2026-10-31   Commit: (pending commit on `kepler/kan-10-credential-reference-via-secretstore`)

## Checks
| Check | Result |
|---|---|
| Lint | PASS — `ruff check adapters api --config pyproject.toml`: 1 import-order issue in the new leakage test auto-fixed; re-run: all checks passed |
| Tests (full suite) | PASS — `python -m pytest adapters api/tests -q`: 55 passed (incl. 4 new tests in `adapters/tests/test_resolve_credential.py` and 1 new test in `api/tests/test_sources_credential_leakage.py`) |
| contract-check | No mismatches: no schema/ontology/harvester-interface change; `resolve_credential` is the only code path that calls `SecretStore.get`; no cloud SDK imports outside `adapters/` (`adapters/secret_store/resolve.py` only imports from `.base`); `.env` remains untracked (`git ls-files` shows only `.env.example`) |
| secret-scan | No secrets found in the diff (only new files: `adapters/secret_store/resolve.py`, `adapters/tests/test_resolve_credential.py`, `api/tests/test_sources_credential_leakage.py`, `spec/changes/kan-10-...`); no key/token/password/connection-string patterns; test secret values (`s3cr3t-value`, `top-s3cr3t`, `sk-live-super-secret-do-not-leak`) are synthetic test fixtures, asserted absent from responses/logs, not real credentials |
| Definition of Done | Met: `resolve_credential` added with tests for success, missing-key (no value leak), and no-logging; API-layer regression test proves a real resolvable secret never appears in the POST /sources response or captured logs; capability spec delta drafted |

## Scenario evidence
| Requirement / Scenario | Evidence (test) | Result |
|---|---|---|
| Credentials are references / resolve-credential-success | `adapters/tests/test_resolve_credential.py::test_resolve_credential_success` — PASS | PASS |
| Credentials are references / resolve-credential-missing-key | `adapters/tests/test_resolve_credential.py::test_resolve_credential_missing_key_raises_without_leaking_value` and `test_resolve_credential_missing_key_error_never_contains_other_env_values` — PASS | PASS |
| Credentials are references / api-never-logs-resolved-secret | `api/tests/test_sources_credential_leakage.py::test_real_secret_value_never_appears_in_response_or_logs` — PASS (plants a real resolvable env value matching `credentials_ref`, asserts it is absent from the HTTP response body and all captured log records) | PASS |
| Credentials are references / read a source (existing, re-run) | `api/tests/test_sources.py::test_register_a_source_stores_active_row_and_returns_id` — PASS (unchanged, still green) | PASS |
| resolve_credential never logs the value | `adapters/tests/test_resolve_credential.py::test_resolve_credential_never_logs_the_value` — PASS | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| credentials_ref is a key resolved by SecretStore | resolve-credential-success, resolve-credential-missing-key | PASS |
| API never stores, logs or returns secret values | register-a-source (existing), api-never-logs-resolved-secret | PASS |

## Not verified
- No harvester exists yet (Epic 3 is later in the build order) to exercise `resolve_credential` in a real end-to-end harvest; this is verified at the unit/contract level only, per the proposal's stated scope and risk note. This is not a gap in this story's AC — the AC is about the registration/credential-reference contract, not harvester execution.
- Docker-secrets-as-env-var behavior was not separately verified beyond `EnvSecretStore` reading `os.environ` (Docker secrets mounted as env vars behave identically; no new adapter code was added for this story).
