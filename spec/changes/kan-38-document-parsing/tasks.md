# Tasks

- [x] 1. Add `document_parsing/models.py` with the `Section` dataclass (heading, level, text, order) (scenario: parse-markdown-sections) - test first
- [x] 2. Add `document_parsing/markdown_parser.py`: section split on ATX headings, body text until next heading, no-heading fallback (scenario: parse-markdown-sections, parse-no-headings-fallback) - test first
- [x] 3. Add `document_parsing/docx_parser.py`: section split on "Heading N" paragraph styles via `python-docx`, no-heading fallback (scenario: parse-docx-sections, parse-no-headings-fallback) - test first
- [x] 4. Add `document_parsing/pdf_parser.py`: section split on font-size/bold heading heuristic via `pypdf`, no-heading fallback (scenario: parse-pdf-sections, parse-no-headings-fallback) - test first
- [x] 5. Add `document_parsing/dispatch.py`: `parse_document` routes by extension (`.md`, `.docx`, `.pdf`), raises on unsupported extensions (scenario: parse-dispatch-by-extension) - test first
- [x] 6. Add idempotency test calling each parser twice on the same fixture (scenario: parse-idempotent) - test first
- [x] 7. Add fixtures: multi-heading and no-heading sample for each of PDF, DOCX, Markdown under `document_parsing/tests/fixtures/` — built in-test with `reportlab`/`python-docx` instead of static files, so fixtures stay in sync with the dataclasses they assert against (no `fixtures/` directory needed)
- [x] 8. Add `document_parsing/requirements.txt` + `requirements-dev.txt` pinning `python-docx`, `pypdf`, `pytest`; register the module with `ruff` in `pyproject.toml`
- [x] 9. Docs and contracts updated: `spec/changes/kan-38-document-parsing/specs/document-parsing.md` delta written (applied to `spec/capabilities/` at archive, per `spec/README.md`); no Confluence Contracts change (no schema/ontology/harvester-interface change)
- [x] 10. `verification.md` completed with evidence per scenario
