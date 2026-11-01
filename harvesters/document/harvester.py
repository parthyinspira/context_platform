"""Document harvester: local-directory source for .md and .xlsx files (KAN-98).

Implements the full `Harvester` interface for a source whose `uri` is a local
directory path.  Supported file types: Markdown (`.md`) and Excel (`.xlsx`).

Each file becomes one `Document` entity and one `Chunk` (body text for
Markdown; column-header description for Excel).  YAML front-matter in `.md`
files provides `title` and `sensitivity`; the defaults are the filename (sans
extension) and `"internal"`.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Optional

import openpyxl
import yaml

from harvesters.base import (
    Chunk,
    ConnectionResult,
    Edge,
    Entity,
    Harvester,
    Profile,
    RawObject,
    ScopeNode,
    ScopeTree,
    ValidationReport,
)
from harvesters.framework import HarvestPlan
from harvesters.registry import register_harvester

_SUPPORTED_SUFFIXES = {".md", ".xlsx"}
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_DEFAULT_SENSITIVITY = "internal"
_ONTOLOGY_VERSION = "v0"


def _external_id(path: str) -> str:
    return f"doc:{path}"


def _parse_md_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter_dict, body_text). frontmatter_dict is {} when absent."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    body = text[match.end():]
    return meta, body


@register_harvester("document")
class DocumentHarvester(Harvester):
    """Harvester for a local directory of Markdown and Excel documents."""

    def connect(self, source: Any) -> ConnectionResult:
        uri = _get_uri(source)
        if not Path(uri).is_dir():
            return ConnectionResult(ok=False, error=f"directory not found: {uri}")
        return ConnectionResult(ok=True)

    def discover(self, source: Any) -> ScopeTree:
        uri = Path(_get_uri(source))
        nodes = []
        for path in sorted(uri.iterdir()):
            if path.suffix in _SUPPORTED_SUFFIXES and path.is_file():
                nodes.append(
                    ScopeNode(
                        id=_external_id(path.name),
                        kind="file",
                        name=path.name,
                        size_hint=path.stat().st_size,
                    )
                )
        return ScopeTree(roots=nodes)

    def profile(self, source: Any, scope: ScopeTree) -> Profile:
        refs = scope.refs()
        counts: dict[str, int] = {}
        for ref in refs:
            suffix = Path(ref.path).suffix or "(none)"
            counts[suffix] = counts.get(suffix, 0) + 1
        return Profile(
            object_count=len(refs),
            total_bytes=sum(r.size_bytes for r in refs),
            counts_by_type=counts,
        )

    def plan(self, profile: Profile) -> HarvestPlan:
        return HarvestPlan(include=("*.md", "*.xlsx"))

    def harvest(
        self, source: Any, plan: HarvestPlan, cursor: Optional[str]
    ) -> Iterable[RawObject]:
        uri = Path(_get_uri(source))
        for ref in self.discover(source).refs():
            if not plan.is_included(ref.path):
                continue
            path = uri / ref.path
            content_type = "text/markdown" if path.suffix == ".md" else (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            yield RawObject(
                external_id=ref.external_id,
                content=path.read_bytes(),
                content_type=content_type,
            )

    def normalize(self, raw: RawObject) -> list[Entity | Edge | Chunk]:
        filename = raw.external_id[len("doc:"):]  # strip "doc:" prefix
        suffix = Path(filename).suffix
        if suffix == ".md":
            return self._normalize_md(raw, filename)
        if suffix == ".xlsx":
            return self._normalize_xlsx(raw, filename)
        return []

    def validate(
        self, plan: HarvestPlan, manifest: list[dict[str, Any]]
    ) -> ValidationReport:
        harvested = {m["external_id"] for m in manifest}
        missing = [
            m["external_id"] for m in manifest
            if m.get("status") != "ok"
        ]
        if missing:
            return ValidationReport(
                status="WARN",
                checks={"harvested": str(len(harvested))},
                errors=[f"incomplete: {m}" for m in missing],
            )
        return ValidationReport(
            status="PASS",
            checks={"harvested": str(len(harvested))},
        )

    # -- internal helpers --------------------------------------------------

    def _normalize_md(self, raw: RawObject, filename: str) -> list[Entity | Edge | Chunk]:
        text = raw.content.decode("utf-8", errors="replace")
        meta, body = _parse_md_frontmatter(text)
        title = meta.get("title") or Path(filename).stem
        sensitivity = str(meta.get("sensitivity") or _DEFAULT_SENSITIVITY)
        entity = Entity(
            type="Document",
            name=title,
            external_id=raw.external_id,
            props={"sensitivity": sensitivity, "title": title, "filename": filename},
            ontology_version=_ONTOLOGY_VERSION,
        )
        chunk = Chunk(
            entity_external_id=raw.external_id,
            text=body.strip(),
            metadata={"filename": filename, "sensitivity": sensitivity},
        )
        return [entity, chunk]

    def _normalize_xlsx(self, raw: RawObject, filename: str) -> list[Entity | Edge | Chunk]:
        import io

        wb = openpyxl.load_workbook(io.BytesIO(raw.content), read_only=True, data_only=True)
        parts: list[str] = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            headers: list[str] = []
            for row in ws.iter_rows(max_row=1, values_only=True):
                headers = [str(c) for c in row if c is not None]
                break
            parts.append(f"Sheet '{sheet_name}': " + ", ".join(headers))
        wb.close()
        summary = "; ".join(parts) if parts else filename
        title = Path(filename).stem
        entity = Entity(
            type="Document",
            name=title,
            external_id=raw.external_id,
            props={"sensitivity": _DEFAULT_SENSITIVITY, "title": title, "filename": filename},
            ontology_version=_ONTOLOGY_VERSION,
        )
        chunk = Chunk(
            entity_external_id=raw.external_id,
            text=summary,
            metadata={"filename": filename, "sensitivity": _DEFAULT_SENSITIVITY},
        )
        return [entity, chunk]


def _get_uri(source: Any) -> str:
    if isinstance(source, dict):
        return source["uri"]
    return getattr(source, "uri")
