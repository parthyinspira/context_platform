# Verification

Status: PASS
Date: 2026-10-31 (round 2 fix same day)   Branch: kepler/kan-82-secret-pii-scanner-redaction

## Checks
| Check | Result |
|---|---|
| Lint | PASS — `ruff check api scheduler adapters --config pyproject.toml`: All checks passed |
| Tests (adapters) | PASS — `python -m pytest adapters/tests -q`: 25 passed (10 scanner tests incl. the round-2 credit-card fix, 1 writer-redaction test, 2 existing writer tests updated for new `metadata.sensitivity` field, rest unaffected) |
| Tests (api) | PASS — `python -m pytest api/tests -q`: 17 passed, unaffected |
| Tests (scheduler) | PASS — `(cd scheduler && python -m pytest -q)`: 1 passed, unaffected |
| contract-check | No mismatches: no schema/ontology/harvester-interface/MCP contract touched (`chunks.metadata` is already `jsonb`, no migration needed); no cloud SDK imports in `adapters/scanning` or `adapters/chunks`; business logic unchanged outside the one wired call site |
| secret-scan | No real secrets found. `git ls-files | grep -E '\.env($|\.)'` -> only `.env.example`. Grepped diff/new files for `BEGIN .*PRIVATE KEY`, `AKIA`, `AIza`, `password=`, `secret=`, `api_key=` — only hits are in `adapters/tests/test_scanner.py` and `adapters/tests/contract/test_chunk_writer.py`, each a clearly-fake, commented seeded fixture (e.g. `AKIAFAKEEXAMPLE12345`, a placeholder PEM block of base64 garbage, `hunter2fakepassword`) used only to prove detection/redaction — none are real credentials |
| spec_check --stage=verify | PASS — see command output below |

```
$ python scripts/spec_check.py spec/changes/kan-82-secret-pii-scanner-redaction --stage=verify
spec_check OK (verify): spec/changes/kan-82-secret-pii-scanner-redaction
```

## Scenario evidence
| Requirement / Scenario | Evidence (test) | Result |
|---|---|---|
| AWS key, token, password, private key detected | `adapters/tests/test_scanner.py::test_detects_and_redacts_aws_key`, `::test_detects_and_redacts_generic_api_token`, `::test_detects_and_redacts_password_assignment`, `::test_detects_and_redacts_private_key_block`, `::test_detects_and_redacts_connection_string_password`, `::test_detects_multiple_secret_kinds_in_one_text` — all PASS | PASS |
| PII detected without a secret | `adapters/tests/test_scanner.py::test_pii_detected_without_a_secret_sets_confidential` — PASS (email + SSN redacted, sensitivity `confidential`) | PASS |
| No findings | `adapters/tests/test_scanner.py::test_no_findings_returns_text_unchanged_and_internal_sensitivity` — PASS (text unchanged, sensitivity `internal`) | PASS |
| Secret outranks PII | `adapters/tests/test_scanner.py::test_secret_outranks_pii_for_sensitivity` — PASS (sensitivity `restricted` when both present) | PASS |
| Redaction before storage | `adapters/tests/contract/test_chunk_writer.py::test_write_redacts_secrets_before_storage_and_sets_sensitivity` — PASS: stored `chunks.text` contains `[REDACTED:aws_access_key_id]`, never the raw fake key; `metadata.sensitivity == "restricted"`, `metadata.redacted is True`; the raw secret is also asserted absent from every call made to the `EmbeddingProvider`, so it is never embedded either | PASS |
| Existing writer behaviour preserved | `adapters/tests/contract/test_chunk_writer.py::test_write_records_embedding_model_from_provider`, `::test_write_defaults_metadata_to_empty_dict` (updated to expect `metadata == {"sensitivity": "internal", ...}` for non-sensitive text) — both PASS | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Detects keys, tokens, passwords in fetched text | AWS key / token / password / private key / connection-string password detected | PASS |
| Redacts before storage | `PostgresChunkWriter.write()` stores redacted text, never the raw secret | PASS |
| Sets sensitivity | `metadata.sensitivity` is `restricted` (secret found), `confidential` (PII only), `internal` (no findings) | PASS |
| Tested with seeded secrets | All scanner and writer tests use fake, clearly-non-real, commented seeded secret values | PASS |

## Review round 2 fix
`story-reviewer` flagged `[blocking]`: `proposal.md` and the spec delta promised credit-card-shaped PII detection that was never implemented or tested. Fixed by adding the `credit_card` pattern to `adapters/scanning/scanner.py` and `test_detects_and_redacts_credit_card_number` to `adapters/tests/test_scanner.py`. Re-ran `python -m pytest adapters/tests -q` (25 passed) and `ruff check adapters --config pyproject.toml` (all checks passed) after the fix. Two `[nit]` (non-blocking) findings were also raised (a two-pass loop in `_derive_sensitivity`, and `metadata["redacted"]` being absent rather than `False` when no findings) — left as-is, consistent with the existing tests and not required for correctness.

## Not verified
- No live `docker compose` run was needed or performed: this change touches only a pure Python module (`adapters/scanning`) and one existing storage adapter (`adapters/chunks/writer.py`), with no new service, route, container, or DB schema — covered entirely by the adapters test suite (24 passed) plus lint. No Docker/DB/credentials were required.
- The actual Git harvester (Epic 3) does not exist yet in this repo, so there is no harvester call site to exercise end-to-end beyond `PostgresChunkWriter`; future harvester code should call `adapters.scanning.scan_and_redact` on fetched text before normalization (noted in `proposal.md` risks).
- High-entropy / ML-based secret detection is out of scope (regex-based deterministic detection only, per project convention and the proposal's stated scope).
