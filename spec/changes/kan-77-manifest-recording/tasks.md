# Tasks

- [ ] 1. Scaffold `harvesters/` package (`__init__.py`, `requirements.txt`, `requirements-dev.txt`, `tests/__init__.py`); add `harvesters` to CI lint and test matrix and to ruff include in `pyproject.toml`
- [ ] 2. Write `harvesters/tests/test_manifest.py` for recording and rules (scenarios: record every outcome with reason, reason required, discover before outcome, one outcome per object, secret in a reason is redacted) - test first
- [ ] 3. Implement `Manifest`, `ManifestEntry`, `Outcome` in `harvesters/manifest.py` to make task 2 pass
- [ ] 4. Write tests for the validator read API and persistence (scenarios: validator reads outcomes and unaccounted objects, manifest persisted and reloaded per run) - test first
- [ ] 5. Implement `by_outcome`, `counts`, `unaccounted`, JSON round trip and `ManifestStore` over `ObjectStore`
- [ ] 6. Lint and full Python test suites pass
- [ ] 7. Docs and contracts reviewed (no schema, ontology or interface signature change; capability delta applied at archive)
- [ ] 8. `contract-check` and `secret-scan` run; verification.md completed
