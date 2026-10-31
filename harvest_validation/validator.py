"""Harvester validator core checks (KAN-83).

Implements the seven checks in scope for this story from the table in
`docs/HARVESTERS.md` section 5: completeness, exclusion integrity, budget
compliance, parse success, ontology conformance, referential integrity and
freshness. Expected yield, secrets/PII, delete sanity and spot check are out
of scope (delete sanity and the publish/quarantine decision already exist in
`harvest_validation/gate.py`, KAN-85).

Consumes the real `harvesters.framework.manifest.Manifest`, `harvesters.
framework.plan.HarvestPlan`, and `harvesters.base.Entity`/`Edge` — no
parallel types. Each `check_*` function returns one `CheckResult`; `validate`
runs all seven and aggregates the worst status into one `ValidationReport`
(see `harvest_validation/report.py`), whose `status` a `PublishQuarantineGate`
can consume directly.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath

from adapters.ontology import ENTITY_TYPES, RELATION_TYPES
from harvest_validation.gate import ValidationStatus
from harvest_validation.report import CheckResult, ValidationReport, build_report
from harvesters.base import Edge, Entity
from harvesters.framework.manifest import Manifest
from harvesters.framework.plan import HarvestPlan

# Maximum sample failures kept per check, so a report stays readable.
MAX_SAMPLES = 5

# Completeness: ratio of fetched to discovered objects.
COMPLETENESS_FAIL_BELOW = 0.80
COMPLETENESS_WARN_BELOW = 0.95

# Parse success: ratio of fetched objects of a type that parsed without error.
PARSE_SUCCESS_FAIL_BELOW = 0.80
PARSE_SUCCESS_WARN_BELOW = 0.95


def _samples(refs: Iterable[str]) -> tuple[str, ...]:
    return tuple(refs)[:MAX_SAMPLES]


def _file_type(ref: str) -> str:
    """Group a ref by extension (without the dot); refs with none group as "noext"."""
    suffix = PurePosixPath(ref).suffix.lstrip(".")
    return suffix or "noext"


def check_completeness(manifest: Manifest) -> CheckResult:
    """Every discovered object is fetched/skipped/failed; fetched/discovered ratio matters."""
    counts = manifest.counts()
    discovered = counts["discovered"]
    fetched = counts["fetched"]
    unaccounted = manifest.unaccounted()

    ratio = 1.0 if discovered == 0 else fetched / discovered

    if ratio < COMPLETENESS_FAIL_BELOW:
        status = ValidationStatus.FAIL
    elif ratio < COMPLETENESS_WARN_BELOW:
        status = ValidationStatus.WARN
    else:
        status = ValidationStatus.PASS

    message = f"fetched {fetched}/{discovered} discovered objects (ratio {ratio:.2f})"
    if unaccounted:
        message += f"; {len(unaccounted)} discovered object(s) have no outcome"

    return CheckResult(
        name="completeness",
        status=status,
        message=message,
        counts=counts,
        samples=_samples(e.ref for e in unaccounted),
    )


def check_exclusion_integrity(plan: HarvestPlan, manifest: Manifest) -> CheckResult:
    """No object matching an exclude pattern was fetched."""
    violations = [
        entry.ref
        for entry in manifest.entries()
        if entry.status == "fetched" and not plan.is_included(entry.ref)
    ]

    if violations:
        return CheckResult(
            name="exclusion_integrity",
            status=ValidationStatus.FAIL,
            message=f"{len(violations)} excluded object(s) were fetched",
            counts={"violations": len(violations)},
            samples=_samples(violations),
        )
    return CheckResult(
        name="exclusion_integrity",
        status=ValidationStatus.PASS,
        message="no excluded object was fetched",
        counts={"violations": 0},
    )


def check_budget_compliance(
    plan: HarvestPlan,
    manifest: Manifest,
    *,
    elapsed_seconds: float | None = None,
    tokens_used: int | None = None,
) -> CheckResult:
    """Files/bytes/time/token budgets on the plan were respected."""
    budgets = plan.budgets
    counts = manifest.counts()
    fetched_count = counts["fetched"]
    fetched_bytes = sum(
        e.size_bytes or 0 for e in manifest.entries() if e.status == "fetched"
    )

    exceeded: list[str] = []
    if budgets.max_files is not None and fetched_count > budgets.max_files:
        exceeded.append("files")
    if budgets.max_bytes is not None and fetched_bytes > budgets.max_bytes:
        exceeded.append("bytes")
    if (
        budgets.max_seconds is not None
        and elapsed_seconds is not None
        and elapsed_seconds > budgets.max_seconds
    ):
        exceeded.append("time")
    max_tokens = budgets.max_tokens
    if max_tokens is not None and tokens_used is not None and tokens_used > max_tokens:
        exceeded.append("tokens")

    if exceeded:
        return CheckResult(
            name="budget_compliance",
            status=ValidationStatus.WARN,
            message=f"budget(s) exceeded: {', '.join(exceeded)}; run marked PARTIAL",
            counts={"fetched_files": fetched_count, "fetched_bytes": fetched_bytes},
            samples=tuple(exceeded),
        )
    return CheckResult(
        name="budget_compliance",
        status=ValidationStatus.PASS,
        message="all budgets respected",
        counts={"fetched_files": fetched_count, "fetched_bytes": fetched_bytes},
    )


# Lower rank = worse, used to pick the single worst status across file types.
_SEVERITY_RANK = {ValidationStatus.FAIL: 0, ValidationStatus.WARN: 1, ValidationStatus.PASS: 2}


def check_parse_success(
    manifest: Manifest, parse_errors: Mapping[str, str] | None = None
) -> CheckResult:
    """Share of fetched objects parsed without error, above a threshold, per type."""
    parse_errors = parse_errors or {}
    fetched_refs = [e.ref for e in manifest.entries() if e.status == "fetched"]

    if not fetched_refs:
        return CheckResult(
            name="parse_success",
            status=ValidationStatus.PASS,
            message="no fetched objects to parse",
            counts={},
        )

    totals: dict[str, int] = {}
    errors_by_type: dict[str, list[str]] = {}
    for ref in fetched_refs:
        file_type = _file_type(ref)
        totals[file_type] = totals.get(file_type, 0) + 1
        if ref in parse_errors:
            errors_by_type.setdefault(file_type, []).append(ref)

    worst = ValidationStatus.PASS
    failing_types: list[str] = []
    warning_types: list[str] = []
    counts: dict[str, int] = {}
    samples: list[str] = []

    for file_type, total in totals.items():
        failed = errors_by_type.get(file_type, [])
        ratio = (total - len(failed)) / total
        counts[f"{file_type}_total"] = total
        counts[f"{file_type}_failed"] = len(failed)
        if ratio < PARSE_SUCCESS_FAIL_BELOW:
            failing_types.append(file_type)
            samples.extend(failed)
            if _SEVERITY_RANK[ValidationStatus.FAIL] < _SEVERITY_RANK[worst]:
                worst = ValidationStatus.FAIL
        elif ratio < PARSE_SUCCESS_WARN_BELOW:
            warning_types.append(file_type)
            samples.extend(failed)
            if _SEVERITY_RANK[ValidationStatus.WARN] < _SEVERITY_RANK[worst]:
                worst = ValidationStatus.WARN

    if failing_types:
        types = ", ".join(sorted(failing_types))
        message = f"parse success below fail threshold for type(s): {types}"
    elif warning_types:
        types = ", ".join(sorted(warning_types))
        message = f"parse success below warn threshold for type(s): {types}"
    else:
        message = "all types parsed above the warn threshold"

    return CheckResult(
        name="parse_success",
        status=worst,
        message=message,
        counts=counts,
        samples=_samples(samples),
    )


def check_ontology_conformance(entities: Iterable[Entity], edges: Iterable[Edge]) -> CheckResult:
    """Every emitted entity/edge uses a known ontology v0 type and carries required fields."""
    violations: list[str] = []

    for entity in entities:
        reasons = []
        if entity.type not in ENTITY_TYPES:
            reasons.append(f"unknown type {entity.type!r}")
        if not entity.external_id:
            reasons.append("missing external_id")
        if not entity.source_id:
            reasons.append("missing source_id")
        if entity.harvested_at is None:
            reasons.append("missing harvested_at")
        if not entity.ontology_version:
            reasons.append("missing ontology_version")
        if reasons:
            violations.append(f"entity {entity.external_id or entity.name!r}: {', '.join(reasons)}")

    for edge in edges:
        reasons = []
        if edge.relation not in RELATION_TYPES:
            reasons.append(f"unknown relation {edge.relation!r}")
        if not edge.src_external_id or not edge.dst_external_id:
            reasons.append("missing endpoint(s)")
        if not edge.source_id:
            reasons.append("missing source_id")
        if edge.harvested_at is None:
            reasons.append("missing harvested_at")
        if not edge.ontology_version:
            reasons.append("missing ontology_version")
        if reasons:
            violations.append(
                f"edge {edge.src_external_id!r}->{edge.dst_external_id!r}: {', '.join(reasons)}"
            )

    if violations:
        return CheckResult(
            name="ontology_conformance",
            status=ValidationStatus.FAIL,
            message=f"{len(violations)} entity/edge record(s) fail ontology conformance",
            counts={"violations": len(violations)},
            samples=_samples(violations),
        )
    return CheckResult(
        name="ontology_conformance",
        status=ValidationStatus.PASS,
        message="every emitted entity and edge conforms to ontology v0",
        counts={"violations": 0},
    )


def check_referential_integrity(
    entities: Iterable[Entity],
    edges: Iterable[Edge],
    *,
    known_external_ids: Iterable[str] = (),
) -> CheckResult:
    """Edges point to an entity emitted this run (or passed in as already known)."""
    known_ids = {e.external_id for e in entities} | set(known_external_ids)

    dangling = [
        f"{edge.src_external_id!r}->{edge.dst_external_id!r}"
        for edge in edges
        if edge.src_external_id not in known_ids or edge.dst_external_id not in known_ids
    ]

    if dangling:
        return CheckResult(
            name="referential_integrity",
            status=ValidationStatus.WARN,
            message=f"{len(dangling)} edge(s) point to an unresolved entity",
            counts={"dangling": len(dangling)},
            samples=_samples(dangling),
        )
    return CheckResult(
        name="referential_integrity",
        status=ValidationStatus.PASS,
        message="every edge resolves to a known entity",
        counts={"dangling": 0},
    )


def check_freshness(
    *,
    cursor_advanced: bool,
    entities: Iterable[Entity] = (),
) -> CheckResult:
    """`harvested_at` is set and the cursor advanced."""
    entities = tuple(entities)
    missing_harvested_at = [e.external_id for e in entities if e.harvested_at is None]

    reasons = []
    if not cursor_advanced:
        reasons.append("cursor did not advance")
    if entities and len(missing_harvested_at) == len(entities):
        reasons.append("no entity has harvested_at set")

    if reasons:
        return CheckResult(
            name="freshness",
            status=ValidationStatus.WARN,
            message="; ".join(reasons),
            counts={"missing_harvested_at": len(missing_harvested_at)},
            samples=_samples(missing_harvested_at),
        )
    return CheckResult(
        name="freshness",
        status=ValidationStatus.PASS,
        message="cursor advanced and harvested_at is set",
        counts={"missing_harvested_at": len(missing_harvested_at)},
    )


def validate(
    plan: HarvestPlan,
    manifest: Manifest,
    entities: Iterable[Entity] = (),
    edges: Iterable[Edge] = (),
    *,
    cursor_advanced: bool = True,
    parse_errors: Mapping[str, str] | None = None,
    elapsed_seconds: float | None = None,
    tokens_used: int | None = None,
    known_external_ids: Iterable[str] = (),
) -> ValidationReport:
    """Run all seven checks and aggregate the worst status into one report."""
    entities = tuple(entities)
    edges = tuple(edges)

    results = (
        check_completeness(manifest),
        check_exclusion_integrity(plan, manifest),
        check_budget_compliance(
            plan, manifest, elapsed_seconds=elapsed_seconds, tokens_used=tokens_used
        ),
        check_parse_success(manifest, parse_errors),
        check_ontology_conformance(entities, edges),
        check_referential_integrity(entities, edges, known_external_ids=known_external_ids),
        check_freshness(cursor_advanced=cursor_advanced, entities=entities),
    )

    return build_report(results)
