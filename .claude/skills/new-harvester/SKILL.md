---
name: new-harvester
description: Scaffold a new harvester pack for a source system (for example SharePoint, Snowflake, Tableau) from the harvester contract. Use for each new source type.
---

Read `docs/HARVESTERS.md` and `spec/capabilities/harvester-framework.md` first. Refine this skill from the first working harvester (Git) once it exists; prefer copying its pattern over inventing a new one.

Create `harvesters/<system>/` with:
1. `harvester.yaml`: capabilities, credential fields, discoverable scope types, default limits and budgets.
2. `harvester.py`: connect, discover (list only, no content), profile (sizes, counts, stacks), plan, harvest (incremental by cursor, idempotent, manifest entries for every object), normalize, validate.
3. `rules/`: deterministic include/exclude, size caps and budgets per object type; version them.
4. `skills/`: short markdown guidance for LLM-assisted planning (inputs, steps, output schema); rules always override a proposed plan.
5. `validator.py`: standard checks plus system-specific ones (expected yield, exclusion integrity).
6. `fixtures/` and tests: plan test, rerun/idempotency test, validator tests with broken fixtures (oversize file, secret, delete spike), budget-hit test.

Rules: read-only credentials, metadata first, no row data by default, secret redaction, secrets via `SecretStore`, register by `source.type`. Add scenarios to the spec delta, and the wizard fields to the UI spec if credentials differ. Run `harvest-dry-run` and `contract-check`.
