"""Request/response models for run create/read/stop and the validation report (KAN-58)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas_discovery import HarvestPlanOut

TERMINAL_RUN_STATES = {"PUBLISHED", "QUARANTINED", "FAILED", "PARTIAL"}


class RunCreate(BaseModel):
    plan: HarvestPlanOut


class RunOut(BaseModel):
    id: str
    source_id: str
    state: str


class ManifestSummaryOut(BaseModel):
    discovered: int = 0
    fetched: int = 0
    skipped: int = 0
    failed: int = 0
    fetched_bytes: int = 0


class LogEntryOut(BaseModel):
    ref: str
    outcome: str | None = None
    outcome_reason: str | None = None


class RunDetailOut(BaseModel):
    id: str
    source_id: str
    state: str
    plan: dict[str, Any]
    manifest_summary: ManifestSummaryOut
    log_entries: list[LogEntryOut] = []
    error: str | None = None


class CheckResultOut(BaseModel):
    name: str
    status: str
    message: str
    counts: dict[str, int] = {}
    samples: list[str] = []


class ValidationReportOut(BaseModel):
    status: str
    checks: list[CheckResultOut] = []
