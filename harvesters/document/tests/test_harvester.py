"""Unit tests for the DocumentHarvester (KAN-98)."""
from __future__ import annotations

import io
from pathlib import Path

import openpyxl
import pytest

from harvesters.base import Chunk, ConnectionResult, Entity, RawObject, ScopeTree
from harvesters.document.harvester import DocumentHarvester, _external_id, _parse_md_frontmatter
from harvesters.framework import HarvestPlan


@pytest.fixture()
def doc_dir(tmp_path: Path) -> Path:
    (tmp_path / "policy.md").write_text(
        "---\ntitle: Policy Doc\nsensitivity: restricted\n---\n\nThe retention period is 7 years.\n",
        encoding="utf-8",
    )
    (tmp_path / "faq.md").write_text(
        "---\ntitle: FAQ\nsensitivity: internal\n---\n\n**Q:** What is X?\n**A:** It is Y.\n",
        encoding="utf-8",
    )
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "summary"
    ws.append(["customer_id", "order_count"])
    ws.append([100, 3])
    xlsx_buf = io.BytesIO()
    wb.save(xlsx_buf)
    (tmp_path / "report.xlsx").write_bytes(xlsx_buf.getvalue())

    (tmp_path / "ignore.txt").write_text("not a doc", encoding="utf-8")
    return tmp_path


class TestConnect:
    def test_ok_for_existing_dir(self, doc_dir: Path) -> None:
        result = DocumentHarvester().connect({"uri": str(doc_dir)})
        assert result == ConnectionResult(ok=True)

    def test_fail_for_missing_dir(self, tmp_path: Path) -> None:
        result = DocumentHarvester().connect({"uri": str(tmp_path / "nonexistent")})
        assert result.ok is False
        assert "not found" in (result.error or "")


class TestDiscover:
    def test_finds_md_and_xlsx_only(self, doc_dir: Path) -> None:
        tree = DocumentHarvester().discover({"uri": str(doc_dir)})
        names = {n.name for n in tree.roots}
        assert names == {"policy.md", "faq.md", "report.xlsx"}
        assert "ignore.txt" not in names

    def test_external_ids_prefixed(self, doc_dir: Path) -> None:
        tree = DocumentHarvester().discover({"uri": str(doc_dir)})
        for node in tree.roots:
            assert node.id.startswith("doc:")


class TestHarvest:
    def test_yields_raw_objects_for_plan(self, doc_dir: Path) -> None:
        h = DocumentHarvester()
        plan = h.plan(h.profile({"uri": str(doc_dir)}, h.discover({"uri": str(doc_dir)})))
        objects = list(h.harvest({"uri": str(doc_dir)}, plan, cursor=None))
        names = {o.external_id for o in objects}
        assert "doc:policy.md" in names
        assert "doc:faq.md" in names
        assert "doc:report.xlsx" in names

    def test_content_type_markdown(self, doc_dir: Path) -> None:
        h = DocumentHarvester()
        plan = HarvestPlan(include=("*.md",))
        objects = list(h.harvest({"uri": str(doc_dir)}, plan, cursor=None))
        md_objs = [o for o in objects if o.external_id.endswith(".md")]
        assert all(o.content_type == "text/markdown" for o in md_objs)


class TestNormalizeMd:
    def _raw(self, filename: str, body: str) -> RawObject:
        return RawObject(
            external_id=_external_id(filename),
            content=body.encode(),
            content_type="text/markdown",
        )

    def test_sensitivity_from_frontmatter(self) -> None:
        raw = self._raw(
            "policy.md",
            "---\ntitle: Policy\nsensitivity: restricted\n---\n\nRetain for 7 years.\n",
        )
        results = DocumentHarvester().normalize(raw)
        entities = [r for r in results if isinstance(r, Entity)]
        assert len(entities) == 1
        assert entities[0].props["sensitivity"] == "restricted"
        assert entities[0].type == "Document"

    def test_default_sensitivity_internal(self) -> None:
        raw = self._raw("notes.md", "# Notes\n\nSome text.\n")
        results = DocumentHarvester().normalize(raw)
        entities = [r for r in results if isinstance(r, Entity)]
        assert entities[0].props["sensitivity"] == "internal"

    def test_chunk_contains_body(self) -> None:
        raw = self._raw(
            "faq.md",
            "---\ntitle: FAQ\nsensitivity: internal\n---\n\n**Q:** What?\n**A:** This.\n",
        )
        results = DocumentHarvester().normalize(raw)
        chunks = [r for r in results if isinstance(r, Chunk)]
        assert len(chunks) == 1
        assert "**Q:**" in chunks[0].text

    def test_chunk_external_id_matches_entity(self) -> None:
        raw = self._raw("doc.md", "No frontmatter body.\n")
        results = DocumentHarvester().normalize(raw)
        entity = next(r for r in results if isinstance(r, Entity))
        chunk = next(r for r in results if isinstance(r, Chunk))
        assert chunk.entity_external_id == entity.external_id


class TestNormalizeXlsx:
    def _raw_xlsx(self, tmp_path: Path) -> RawObject:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "orders"
        ws.append(["order_id", "amount"])
        buf = io.BytesIO()
        wb.save(buf)
        return RawObject(
            external_id=_external_id("report.xlsx"),
            content=buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_document_entity_created(self, tmp_path: Path) -> None:
        raw = self._raw_xlsx(tmp_path)
        results = DocumentHarvester().normalize(raw)
        entities = [r for r in results if isinstance(r, Entity)]
        assert len(entities) == 1
        assert entities[0].type == "Document"

    def test_chunk_contains_headers(self, tmp_path: Path) -> None:
        raw = self._raw_xlsx(tmp_path)
        results = DocumentHarvester().normalize(raw)
        chunks = [r for r in results if isinstance(r, Chunk)]
        assert len(chunks) == 1
        assert "order_id" in chunks[0].text
        assert "amount" in chunks[0].text


class TestParseMdFrontmatter:
    def test_parses_yaml_block(self) -> None:
        meta, body = _parse_md_frontmatter("---\ntitle: T\nsensitivity: internal\n---\n\nBody.\n")
        assert meta == {"title": "T", "sensitivity": "internal"}
        assert "Body." in body

    def test_no_frontmatter_returns_empty_dict(self) -> None:
        meta, body = _parse_md_frontmatter("# Heading\n\nContent.\n")
        assert meta == {}
        assert "Heading" in body


class TestValidate:
    def test_pass_when_all_ok(self) -> None:
        manifest = [{"external_id": "doc:a.md", "status": "ok"}]
        report = DocumentHarvester().validate(HarvestPlan(), manifest)
        assert report.status == "PASS"

    def test_warn_when_incomplete(self) -> None:
        manifest = [{"external_id": "doc:a.md", "status": "error"}]
        report = DocumentHarvester().validate(HarvestPlan(), manifest)
        assert report.status == "WARN"
        assert report.errors
