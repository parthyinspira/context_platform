# Tasks

- [x] 1. Migration `0004_harvest_runs` up/down + contract test (scenario: harvest-runs-table-created, harvest-runs-accepts-valid-states, harvest-runs-rejects-invalid-state, migration-up-creates-table, migration-down-drops-table, migration-reapply-is-no-op) - test first
- [x] 2. `harvesters/base.py`: extend the existing `Harvester` ABC (from KAN-12) in place to the full seven-method lifecycle + new supporting dataclasses + `HarvestRunState` enum, reusing `harvesters.framework.HarvestPlan` (KAN-76) for `plan()`; update `harvesters/tests/{test_base,test_registry,fixtures}.py` accordingly (scenario: harvester-interface-has-all-stages, abstract-class-cannot-skip-a-method, base-class-contract, cannot-instantiate-incomplete-subclass)
- [x] 3. Docs and contracts updated (`spec/capabilities/harvester-framework.md` "Base class and plugin registry" requirement; no Confluence edit needed, contract shape unchanged from `docs/HARVESTERS.md`)
- [x] 4. verification.md completed
