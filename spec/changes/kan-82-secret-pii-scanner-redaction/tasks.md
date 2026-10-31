# Tasks

- [x] 1. Write `adapters/tests/test_scanner.py` with seeded fake secrets (AWS-shaped key, generic API token, PEM private key block, password assignment, connection-string password) and PII (email, SSN) asserting detection, redaction and sensitivity derivation (scenarios: AWS key/token/password/private key detected, PII detected without a secret, no findings) - test first
- [x] 2. Add `adapters/scanning/scanner.py` + `adapters/scanning/__init__.py`: deterministic regex-based `scan_and_redact(text) -> ScanResult` (redacted_text, findings, sensitivity)
- [x] 3. Write `adapters/tests/contract/test_chunk_writer.py` addition (or new test file) proving `PostgresChunkWriter.write()` stores redacted text and sets `metadata.sensitivity` (scenario: redaction before storage) - test first for the wiring
- [x] 4. Wire `scan_and_redact` into `adapters/chunks/writer.py` `PostgresChunkWriter.write()` before embedding/storing
- [x] 5. Run tests (`adapters/tests`) and confirm all pass
- [x] 6. Docs and contracts reviewed (spec/capabilities/harvester-framework.md delta applied at archive; no schema/ontology/harvester-interface change — `chunks.metadata` jsonb already supports sensitivity)
- [x] 7. `contract-check` and `secret-scan` run clean (seeded test secrets are clearly fake and isolated to test files)
- [x] 8. verification.md completed
