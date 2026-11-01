"""Request/response models for test-connection, discover and plan-preview (KAN-58)."""
from __future__ import annotations

from pydantic import BaseModel


class TestConnectionRequest(BaseModel):
    type: str
    uri: str
    credentials_ref: str | None = None


class ConnectionResultOut(BaseModel):
    ok: bool
    error: str | None = None


class ScopeNodeOut(BaseModel):
    id: str
    kind: str
    name: str
    size_hint: int | None = None
    children: list["ScopeNodeOut"] = []


class ScopeTreeOut(BaseModel):
    roots: list[ScopeNodeOut] = []


class PlanRequest(BaseModel):
    selected_refs: list[str] | None = None


class BudgetsOut(BaseModel):
    max_files: int | None = None
    max_bytes: int | None = None
    max_seconds: float | None = None
    max_tokens: int | None = None


class HarvestPlanOut(BaseModel):
    include: list[str] = []
    exclude: list[str] = []
    size_cap_bytes: int | None = None
    budgets: BudgetsOut = BudgetsOut()


class ProfileOut(BaseModel):
    object_count: int
    total_bytes: int
    detected_stacks: list[str] = []
    counts_by_type: dict[str, int] = {}


class PlanPreviewOut(BaseModel):
    plan: HarvestPlanOut
    profile: ProfileOut
    estimated_bytes: int
    estimated_files: int
    estimated_seconds: float
    estimated_tokens: int
    budget_warnings: list[str] = []
