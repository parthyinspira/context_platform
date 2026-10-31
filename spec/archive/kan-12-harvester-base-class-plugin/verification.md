# Verification

Status: PASS
Date: 2026-10-31   Commit: d3a6344e4134035a5cb9511fee7b6802fff6e678 (+ working tree: harvesters/, spec/changes/kan-12-harvester-base-class-plugin/, pyproject.toml, .github/workflows/ci.yml)

## Checks
| Check | Result |
|---|---|
| Lint (`ruff check api scheduler adapters ontology harvesters`) | PASS for `harvesters` (0 errors). Pre-existing `api/tests/test_source_registered_consumer.py` I001 import-order finding reproduces identically on `main` before this change (verified with `git stash`); unrelated to this story, not fixed here. |
| Tests (`pytest harvesters/tests -q`) | PASS: 7 passed |
| `docker compose up` exercised | Not applicable: this story adds a library package only, no service/container changes |
| contract-check | See "Contract check" below: one documented, pre-approved scope narrowing (see proposal.md Risks); no schema/ontology/MCP/adapter/secret mismatches |
| Definition of Done | Met for the scope in `proposal.md` (discover/fetch/normalize base class + source.type registry); full 7-stage harvester lifecycle intentionally out of scope |

## Contract check
- Schema: no table/column changes; no migration needed.
- Ontology: `Entity`/`Edge`/`Chunk` dataclasses in `harvesters/base.py` mirror the `entities`/`edges`/`chunks` column shapes in `CLAUDE.md`'s "Postgres schema v0"; no new ontology types introduced.
- Harvester interface: `docs/HARVESTERS.md` section 2 specifies a 7-method interface (`connect/discover/profile/plan/harvest/normalize/validate`) for a fully built harvester pack. This story implements only the 3-method interface named in the KAN-12 Jira AC and in `CLAUDE.md`'s top-level "Harvester interface" contract (`discover/fetch/normalize`), as the shared base a concrete harvester (Git, in a later story) will extend. This is called out in `proposal.md` under "Risks and open questions" as an explicit, pre-approved scope decision, not a silent contract change. No existing contract text was edited.
- Adapters: no cloud SDK imports in `harvesters/` (`grep -rnE "google\.cloud|azure|boto3" harvesters` -> no matches); no business logic needed an adapter in this story.
- MCP tools: not touched.
- Secrets: no secret-shaped strings in the diff or in `harvesters/`; `git ls-files | grep -E "\.env($|\.)"` shows only `.env.example` tracked.
- Docs: no contract text changed (the `discover/fetch/normalize` interface text in `CLAUDE.md` is unchanged, now implemented in code), so no Confluence Contracts update is required for this story.

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Base class and plugin registry / base-class-contract | `harvesters/tests/test_base.py::test_base_class_contract_full_implementation` | PASS |
| Base class and plugin registry / cannot-instantiate-incomplete-subclass | `harvesters/tests/test_base.py::test_cannot_instantiate_incomplete_subclass`, `test_cannot_instantiate_base_class_directly` | PASS |
| Base class and plugin registry / registry-lookup-by-type | `harvesters/tests/test_registry.py::test_registry_lookup_by_type_returns_instance_of_registered_class`, `test_registry_lookup_is_per_type` | PASS |
| Base class and plugin registry / unknown-type-raises | `harvesters/tests/test_registry.py::test_unknown_type_raises_with_type_name` | PASS |
| Base class and plugin registry / duplicate-registration-rejected | `harvesters/tests/test_registry.py::test_duplicate_registration_rejected` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| 1. discover/fetch/normalize interface implemented | base-class-contract, cannot-instantiate-incomplete-subclass | PASS |
| 2. harvester chosen by source.type | registry-lookup-by-type, unknown-type-raises, duplicate-registration-rejected | PASS |

## Not verified
- `docker compose up` / container behavior: not applicable, no service changed in this story.
- The full `connect/profile/plan/harvest/validate` lifecycle, budgets, size caps, manifest recording and validator from `docs/HARVESTERS.md`: explicitly out of scope for KAN-12 (see proposal.md); will be exercised once a concrete harvester (Git, KAN-13+) is built on this base.
- Linux vs Windows parity for this package: pure-Python, no OS-specific code; tests run on Windows in this session only.
