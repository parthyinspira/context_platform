"""Harvest run manifest (KAN-77).

Implements `docs/HARVESTERS.md` rule 11: every discovered, fetched, skipped and
failed object is recorded with a reason, and the validator reads the result.

A `Manifest` belongs to one source and one run. Objects are keyed by a stable
ref (a path or `external_id`). Rules:
- every record needs a non-empty reason;
- an object must be discovered before it gets an outcome;
- each object gets at most one outcome (fetched, skipped or failed); an
  identical repeat is a no-op so a resumed run can replay its records.

Reasons pass through the shared secret/PII scanner before storage, so error
text that holds a credential is never kept. Persistence goes through the
cloud-neutral `ObjectStore` interface at `manifests/<source_id>/<run_id>.json`.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum

from adapters.object_store import ObjectStore
from adapters.scanning import scan_and_redact

MANIFEST_FORMAT_VERSION = 1
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class ManifestError(ValueError):
    """A record breaks a manifest rule; the manifest is left unchanged."""


class Outcome(StrEnum):
    FETCHED = "fetched"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class ManifestEntry:
    ref: str
    discovery_reason: str
    discovered_at: datetime
    size_bytes: int | None = None
    outcome: Outcome | None = None
    outcome_reason: str | None = None
    outcome_at: datetime | None = None

    @property
    def status(self) -> str:
        """`discovered` until an outcome is recorded, then the outcome value."""
        return self.outcome.value if self.outcome else "discovered"

    def to_dict(self) -> dict:
        return {
            "ref": self.ref,
            "discovery_reason": self.discovery_reason,
            "discovered_at": self.discovered_at.isoformat(),
            "size_bytes": self.size_bytes,
            "outcome": self.outcome.value if self.outcome else None,
            "outcome_reason": self.outcome_reason,
            "outcome_at": self.outcome_at.isoformat() if self.outcome_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ManifestEntry:
        return cls(
            ref=data["ref"],
            discovery_reason=data["discovery_reason"],
            discovered_at=datetime.fromisoformat(data["discovered_at"]),
            size_bytes=data.get("size_bytes"),
            outcome=Outcome(data["outcome"]) if data.get("outcome") else None,
            outcome_reason=data.get("outcome_reason"),
            outcome_at=(
                datetime.fromisoformat(data["outcome_at"]) if data.get("outcome_at") else None
            ),
        )


def _check_id(name: str, value: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ManifestError(f"{name} must be a non-empty id of letters, digits, '.', '_' or '-'")
    return value


def _clean_reason(reason: str | None) -> str:
    if not isinstance(reason, str) or not reason.strip():
        raise ManifestError("a non-empty reason is required for every manifest record")
    return scan_and_redact(reason.strip()).redacted_text


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Manifest:
    """Per-run record of every object a harvester discovered and what happened to it."""

    def __init__(
        self,
        source_id: str,
        run_id: str,
        now: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.source_id = _check_id("source_id", source_id)
        self.run_id = _check_id("run_id", run_id)
        self._now = now
        self._entries: dict[str, ManifestEntry] = {}

    # Recording -----------------------------------------------------------

    def discovered(self, ref: str, reason: str, size_bytes: int | None = None) -> ManifestEntry:
        if not isinstance(ref, str) or not ref.strip():
            raise ManifestError("ref must be a non-empty string")
        if size_bytes is not None and size_bytes < 0:
            raise ManifestError("size_bytes must be zero or more")
        clean = _clean_reason(reason)
        existing = self._entries.get(ref)
        if existing is not None:
            if existing.discovery_reason == clean and existing.size_bytes == size_bytes:
                return existing
            raise ManifestError(f"{ref!r} already discovered with a different reason or size")
        entry = ManifestEntry(
            ref=ref, discovery_reason=clean, discovered_at=self._now(), size_bytes=size_bytes
        )
        self._entries[ref] = entry
        return entry

    def fetched(self, ref: str, reason: str) -> ManifestEntry:
        return self._record_outcome(ref, Outcome.FETCHED, reason)

    def skipped(self, ref: str, reason: str) -> ManifestEntry:
        return self._record_outcome(ref, Outcome.SKIPPED, reason)

    def failed(self, ref: str, reason: str) -> ManifestEntry:
        return self._record_outcome(ref, Outcome.FAILED, reason)

    def _record_outcome(self, ref: str, outcome: Outcome, reason: str) -> ManifestEntry:
        clean = _clean_reason(reason)
        existing = self._entries.get(ref)
        if existing is None:
            raise ManifestError(f"{ref!r} was not discovered; discover before {outcome.value}")
        if existing.outcome is not None:
            if existing.outcome is outcome and existing.outcome_reason == clean:
                return existing
            raise ManifestError(
                f"{ref!r} already {existing.outcome.value}; one outcome per object"
            )
        entry = replace(existing, outcome=outcome, outcome_reason=clean, outcome_at=self._now())
        self._entries[ref] = entry
        return entry

    # Reading (validator API) ---------------------------------------------

    def get(self, ref: str) -> ManifestEntry:
        return self._entries[ref]

    def entries(self) -> list[ManifestEntry]:
        """All entries, sorted by ref for deterministic reports."""
        return [self._entries[k] for k in sorted(self._entries)]

    def by_outcome(self, outcome: Outcome) -> list[ManifestEntry]:
        return [e for e in self.entries() if e.outcome is outcome]

    def unaccounted(self) -> list[ManifestEntry]:
        """Discovered objects with no outcome yet (input to the completeness check)."""
        return [e for e in self.entries() if e.outcome is None]

    def counts(self) -> dict[str, int]:
        entries = self.entries()
        counts = {"discovered": len(entries)}
        for outcome in Outcome:
            counts[outcome.value] = sum(1 for e in entries if e.outcome is outcome)
        counts["unaccounted"] = sum(1 for e in entries if e.outcome is None)
        return counts

    # Serialization -------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "format_version": MANIFEST_FORMAT_VERSION,
            "source_id": self.source_id,
            "run_id": self.run_id,
            "entries": [e.to_dict() for e in self.entries()],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_dict(cls, data: dict, now: Callable[[], datetime] = _utcnow) -> Manifest:
        if data.get("format_version") != MANIFEST_FORMAT_VERSION:
            raise ManifestError(f"unsupported manifest format_version {data.get('format_version')}")
        manifest = cls(source_id=data["source_id"], run_id=data["run_id"], now=now)
        for raw in data["entries"]:
            entry = ManifestEntry.from_dict(raw)
            manifest._entries[entry.ref] = entry
        return manifest

    @classmethod
    def from_json(cls, text: str, now: Callable[[], datetime] = _utcnow) -> Manifest:
        return cls.from_dict(json.loads(text), now=now)


class ManifestStore:
    """Saves and loads manifests through the `ObjectStore` interface."""

    def __init__(self, object_store: ObjectStore) -> None:
        self._store = object_store

    @staticmethod
    def key(source_id: str, run_id: str) -> str:
        return f"manifests/{_check_id('source_id', source_id)}/{_check_id('run_id', run_id)}.json"

    def save(self, manifest: Manifest) -> str:
        key = self.key(manifest.source_id, manifest.run_id)
        self._store.put(key, manifest.to_json().encode("utf-8"))
        return key

    def load(self, source_id: str, run_id: str) -> Manifest:
        data = self._store.get(self.key(source_id, run_id))
        return Manifest.from_json(data.decode("utf-8"))
