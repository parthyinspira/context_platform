# KAN-38: Document parsing for PDF, DOCX and Markdown

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-38   Epic: 7 Upload harvester (KAN-36)   Branch: kepler/kan-38-document-parsing-pdf-docx

## Why
Epic 7 (Upload harvester) needs to turn raw uploaded files into text before anything can be normalized into `Document` entities and `chunks`. KAN-37 (upload trigger) and KAN-39 (normalization: entities/chunks/embeddings stored) are separate stories; this story only covers getting structured, section-aware text out of the three most common upload formats (PDF, DOCX, Markdown), per `docs/HACKATHON_SCOPE.md`'s "Upload / documents (docx, pdf, md, xlsx)" and `docs/HARVESTERS.md`'s rule to chunk by structure (section/heading), not fixed windows. xlsx is out of scope here (tracked separately; HACKATHON_SCOPE treats xlsx as structure-only, not prose).

## What changes
- Add a `document_parsing` library module with one parser per format (PDF, DOCX, Markdown) behind a common interface.
- Each parser extracts plain text and splits it into an ordered list of `Section` records (heading text, heading level, body text, order) using each format's native structure (Markdown headings, DOCX heading styles, PDF-detected headings/font-size heuristics), falling back to a single untitled section when a document has no detected headings.
- A thin dispatcher (`parse_document(path_or_bytes, filename) -> list[Section]`) picks the parser by file extension.
- No DB, harvester lifecycle (connect/discover/plan/validate), entity/chunk writes, or embeddings — that is KAN-37 and KAN-39.

## In scope
- `document_parsing/` module: `models.py` (`Section` dataclass), `markdown_parser.py`, `docx_parser.py`, `pdf_parser.py`, `dispatch.py`.
- Fixture documents (PDF, DOCX, MD) with multiple headings/sections for tests, plus a no-heading fixture per format.
- Unit tests per parser and for the dispatcher, including idempotency (same input parses to the same output) and the no-heading fallback.
- Dependency additions (`python-docx`, `pypdf` or similar) scoped to this module's `requirements.txt`.

## Out of scope
- xlsx parsing (different shape: structure-only, not prose; not in this story's AC).
- Upload trigger / `ObjectStore` wiring (KAN-37).
- Storing `Document` entities, `chunks`, embeddings, or running the ontology updater (KAN-39).
- Harvester lifecycle states, validator, budgets (this module has no run/manifest yet; it is invoked by the future upload harvester).
- Schema or ontology changes (none needed: this story produces in-memory `Section` objects only).

## Acceptance criteria (from Jira)
1. Text extracted with section structure, for PDF, DOCX and Markdown -> scenarios: parse-markdown-sections, parse-docx-sections, parse-pdf-sections, parse-no-headings-fallback, parse-dispatch-by-extension, parse-idempotent

## Affected
Capabilities: `spec/capabilities/document-parsing.md` (new)   Docs/contracts: none (no schema, ontology or harvester-interface change; `document_parsing` is a plain library module consumed by the future upload harvester, not the `Harvester` interface itself)

## Risks and open questions
- PDF heading detection has no reliable semantic markup (unlike DOCX styles or Markdown `#`), so this story uses a font-size/boldness heuristic via `pypdf`/`pdfminer`-style text extraction; accuracy on exotic PDF layouts is a known limitation, called out in `verification.md` if observed.
- Library choice for PDF/DOCX extraction is pinned in `document_parsing/requirements.txt`; no cloud SDK involved, so no `adapters/` placement needed.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
