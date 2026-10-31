# Tasks

- [x] 1. Write `adapters/tests/test_resolve_credential.py` covering resolve success, missing key (error carries only the key, no value), and a no-logging assertion (scenarios: resolve-credential-success, resolve-credential-missing-key) - test first
- [x] 2. Add `adapters/secret_store/resolve.py`: `CredentialNotFoundError` and `resolve_credential(credentials_ref, secret_store) -> str`
- [x] 3. Write `api/tests/test_sources_credential_leakage.py` proving a real resolvable secret value never appears in the POST /sources request/response cycle or captured logs (scenario: api-never-logs-resolved-secret)
- [x] 4. Run `python -m pytest adapters api/tests -q` and confirm all pass (55 passed)
- [x] 5. Update `spec/capabilities/source-registry.md`-matching delta already drafted in `specs/source-registry.md` (applied at archive)
- [x] 6. `contract-check` and `secret-scan` run clean
- [x] 7. verification.md completed
