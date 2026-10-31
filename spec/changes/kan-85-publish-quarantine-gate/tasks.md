# Tasks

- [x] 1. `harvest_validation` package skeleton: `RunState` enum, `ValidationStatus` enum, `GateResult`, `InvalidRunStateError` (scenario: gate-rejects-non-validating-state) - test first
- [x] 2. `PublishQuarantineGate.evaluate()` FAIL path -> QUARANTINED, published=False (scenario: failed-validation-quarantines)
- [x] 3. `PublishQuarantineGate.evaluate()` WARN path -> PUBLISHED, published=True, warning=True (scenario: warn-validation-publishes-with-warning)
- [x] 4. `PublishQuarantineGate.evaluate()` PASS path -> PUBLISHED, published=True, warning=False (scenario: pass-validation-publishes)
- [x] 5. State guard: evaluate() from any non-VALIDATING state raises InvalidRunStateError (scenario: gate-rejects-non-validating-state)
- [x] 6. Wire package into `pyproject.toml` ruff include, CI matrix, and `requirements*.txt`
- [x] 7. Docs and contracts updated (spec delta applied to `spec/capabilities/harvest-validation.md` at archive time; no CLAUDE.md/Confluence contract change needed)
- [x] 8. verification.md completed
