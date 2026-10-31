# Tasks

- [x] 1. Write failing tests for the `Harvester` base class contract (scenario: base-class-contract, cannot-instantiate-incomplete-subclass) - test first
- [x] 2. Implement `harvesters/base.py` (`Harvester` ABC, `ObjectRef`, `RawObject`, `Entity`, `Edge`, `Chunk`) to pass those tests
- [x] 3. Write failing tests for the plugin registry (scenario: registry-lookup-by-type, unknown-type-raises, duplicate-registration-rejected) - test first
- [x] 4. Implement `harvesters/registry.py` (`register_harvester`, `get_harvester`, `UnknownSourceTypeError`) to pass those tests
- [x] 5. Add `harvesters/__init__.py` and fixture harvesters under `harvesters/tests/fixtures.py` used only by tests
- [x] 6. Update `spec/capabilities/harvester-framework.md` with the new requirement (delta in `specs/harvester-framework.md`)
- [x] 7. Run `ruff check harvesters` (added `harvesters/**/*.py` to `pyproject.toml` ruff include, and `harvesters` to CI lint/test matrix) and `pytest harvesters`
- [x] 8. Run `contract-check` and `secret-scan` skills
- [x] 9. verification.md completed
