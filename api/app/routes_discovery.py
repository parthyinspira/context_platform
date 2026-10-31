"""Test-connection, discover and plan-preview routes (KAN-58).

These are cheap, synchronous pre-harvest steps, run in-process against the
registered `Harvester` for a source's type (see `harvesters.registry`) —
unlike the actual `harvest()` step, which runs as a separate one-off
container (`harvesters/run.py`).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.main import connection_factory_dependency
from app.schemas_discovery import (
    BudgetsOut,
    ConnectionResultOut,
    HarvestPlanOut,
    PlanPreviewOut,
    PlanRequest,
    ProfileOut,
    ScopeNodeOut,
    ScopeTreeOut,
    TestConnectionRequest,
)
from harvesters.base import Profile, ScopeNode, ScopeTree
from harvesters.framework import HarvestPlan
from harvesters.registry import UnknownSourceTypeError, get_harvester

router = APIRouter()

# Rough, documented heuristics (no real estimator exists yet): ~1 MB/s pull
# throughput and ~4 bytes/token, good enough for a hackathon plan preview.
_BYTES_PER_SECOND_ESTIMATE = 1_000_000
_BYTES_PER_TOKEN_ESTIMATE = 4


def _get_harvester_or_400(source_type: str) -> Any:
    try:
        return get_harvester(source_type)
    except UnknownSourceTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _load_source(connection_factory: Any, source_id: str) -> dict[str, Any] | None:
    conn = connection_factory()
    cur = conn.cursor()
    cur.execute("SELECT id, type, uri FROM sources WHERE id = %s", (source_id,))
    row = cur.fetchone()
    if row is None:
        return None
    return {"id": str(row[0]), "type": row[1], "uri": row[2]}


def _scope_node_out(node: ScopeNode) -> ScopeNodeOut:
    return ScopeNodeOut(
        id=node.id,
        kind=node.kind,
        name=node.name,
        size_hint=node.size_hint,
        children=[_scope_node_out(child) for child in node.children],
    )


def _scope_tree_out(tree: ScopeTree) -> ScopeTreeOut:
    return ScopeTreeOut(roots=[_scope_node_out(root) for root in tree.roots])


def _plan_out(plan: HarvestPlan) -> HarvestPlanOut:
    return HarvestPlanOut(
        include=list(plan.include),
        exclude=list(plan.exclude),
        size_cap_bytes=plan.size_cap_bytes,
        budgets=BudgetsOut(
            max_files=plan.budgets.max_files,
            max_bytes=plan.budgets.max_bytes,
            max_seconds=plan.budgets.max_seconds,
            max_tokens=plan.budgets.max_tokens,
        ),
    )


def _profile_out(profile: Profile) -> ProfileOut:
    return ProfileOut(
        object_count=profile.object_count,
        total_bytes=profile.total_bytes,
        detected_stacks=list(profile.detected_stacks),
        counts_by_type=dict(profile.counts_by_type),
    )


def _budget_warnings(
    plan: HarvestPlan, estimated_bytes: int, estimated_files: int,
    estimated_seconds: float, estimated_tokens: int,
) -> list[str]:
    warnings: list[str] = []
    budgets = plan.budgets
    if budgets.max_bytes is not None and estimated_bytes > budgets.max_bytes:
        warnings.append(
            f"estimated bytes ({estimated_bytes}) exceed budget max_bytes ({budgets.max_bytes})"
        )
    if budgets.max_files is not None and estimated_files > budgets.max_files:
        warnings.append(
            f"estimated files ({estimated_files}) exceed budget max_files ({budgets.max_files})"
        )
    if budgets.max_seconds is not None and estimated_seconds > budgets.max_seconds:
        warnings.append(
            f"estimated time ({estimated_seconds:.0f}s) exceeds budget max_seconds "
            f"({budgets.max_seconds})"
        )
    if budgets.max_tokens is not None and estimated_tokens > budgets.max_tokens:
        warnings.append(
            f"estimated tokens ({estimated_tokens}) exceed budget max_tokens ({budgets.max_tokens})"
        )
    return warnings


@router.post(
    "/sources/test-connection",
    response_model=ConnectionResultOut,
    summary="Test credentials for a not-yet-created source",
    description="Calls the registered harvester's connect() for the given type/uri/"
    "credentials_ref and reports ok/error. Never echoes the credential value back.",
)
def test_connection(request: TestConnectionRequest) -> ConnectionResultOut:
    harvester = _get_harvester_or_400(request.type)
    result = harvester.connect(
        {"type": request.type, "uri": request.uri, "credentials_ref": request.credentials_ref}
    )
    return ConnectionResultOut(ok=result.ok, error=result.error)


@router.post(
    "/sources/{source_id}/discover",
    response_model=ScopeTreeOut,
    summary="Discover a source's scope tree",
    description="Connects to the source and lists what is available (repos/databases/"
    "sites), metadata only, as a nested scope tree.",
)
def discover_source(
    source_id: str,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> ScopeTreeOut:
    source = _load_source(connection_factory, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    harvester = _get_harvester_or_400(source["type"])
    connection_result = harvester.connect(source)
    if not connection_result.ok:
        raise HTTPException(status_code=400, detail=f"connect failed: {connection_result.error}")
    tree = harvester.discover(source)
    return _scope_tree_out(tree)


@router.post(
    "/sources/{source_id}/plan",
    response_model=PlanPreviewOut,
    summary="Preview the harvest plan for a selected scope",
    description="Profiles an optional subset of the discovered scope and returns the "
    "resulting harvest plan, byte/file/time/token estimates and any budget warnings.",
)
def plan_source(
    source_id: str,
    request: PlanRequest,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> PlanPreviewOut:
    source = _load_source(connection_factory, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    harvester = _get_harvester_or_400(source["type"])
    connection_result = harvester.connect(source)
    if not connection_result.ok:
        raise HTTPException(status_code=400, detail=f"connect failed: {connection_result.error}")

    tree = harvester.discover(source)
    if request.selected_refs is not None:
        selected = set(request.selected_refs)
        refs = [r for r in tree.refs() if r.external_id in selected]
        tree = ScopeTree(
            roots=[
                ScopeNode(id=r.external_id, kind="file", name=r.path, size_hint=r.size_bytes)
                for r in refs
            ]
        )

    profile = harvester.profile(source, tree)
    plan = harvester.plan(profile)

    estimated_bytes = profile.total_bytes
    estimated_files = profile.object_count
    estimated_seconds = max(1.0, estimated_bytes / _BYTES_PER_SECOND_ESTIMATE)
    estimated_tokens = estimated_bytes // _BYTES_PER_TOKEN_ESTIMATE

    return PlanPreviewOut(
        plan=_plan_out(plan),
        profile=_profile_out(profile),
        estimated_bytes=estimated_bytes,
        estimated_files=estimated_files,
        estimated_seconds=estimated_seconds,
        estimated_tokens=estimated_tokens,
        budget_warnings=_budget_warnings(
            plan, estimated_bytes, estimated_files, estimated_seconds, estimated_tokens
        ),
    )
