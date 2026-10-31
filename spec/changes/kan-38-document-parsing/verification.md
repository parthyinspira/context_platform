# Verification

Status: PASS
Date: 2026-10-31   Commit: (pending commit on kepler/kan-38-document-parsing-pdf-docx)

## Checks
| Check | Result |
|---|---|
| Lint | `ruff check document_parsing pyproject.toml` — all checks passed |
| Tests (full suite) | `python -m pytest document_parsing -q` — 13/13 passed |
| docker compose up exercised | Not applicable — this change is a plain Python library module with no service, container or compose entry (no `Dockerfile`/compose wiring in scope for this story) |
| contract-check | No schema, ontology, harvester-interface, MCP or cloud-SDK changes in this diff; no mismatches found |
| secret-scan | No secrets found in `document_parsing/` or the change folder; `.env.example` is the only tracked env file |
| Definition of Done | All tasks in `tasks.md` ticked |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Section-structured extraction / parse-markdown-sections | `document_parsing/tests/test_markdown_parser.py::test_parse_markdown_sections` | PASS |
| Section-structured extraction / parse-docx-sections | `document_parsing/tests/test_docx_parser.py::test_parse_docx_sections` | PASS |
| Section-structured extraction / parse-pdf-sections | `document_parsing/tests/test_pdf_parser.py::test_parse_pdf_sections` | PASS |
| Fallback for no headings / parse-no-headings-fallback | `test_markdown_parser.py::test_parse_markdown_no_headings_fallback`, `test_docx_parser.py::test_parse_docx_no_headings_fallback`, `test_pdf_parser.py::test_parse_pdf_no_headings_fallback` | PASS |
| Format dispatch by extension / parse-dispatch-by-extension | `document_parsing/tests/test_dispatch.py::test_parse_document_routes_markdown`, `::test_parse_document_routes_docx`, `::test_parse_document_routes_pdf`, `::test_parse_document_rejects_unsupported_extension` | PASS |
| Idempotent parsing / parse-idempotent | `test_markdown_parser.py::test_parse_markdown_idempotent`, `test_docx_parser.py::test_parse_docx_idempotent`, `test_pdf_parser.py::test_parse_pdf_idempotent` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Text extracted with section structure, for PDF, DOCX and Markdown | parse-markdown-sections, parse-docx-sections, parse-pdf-sections, parse-no-headings-fallback, parse-dispatch-by-extension, parse-idempotent | PASS |

## Not verified
- **PDF heading detection on real-world/exotic layouts**: the PDF parser uses a font-size heuristic (`pdf_parser.py`'s `_HEADING_SIZE_RATIO`) validated against a synthetic fixture built with `reportlab` (clear font-size contrast between headings and body). It has not been exercised against scanned PDFs, PDFs with inconsistent or embedded-font metrics, or multi-column layouts; accuracy on such documents is a known limitation called out in `proposal.md`'s "Risks and open questions". Not a blocker for this story's AC, which is scoped to structural extraction working on well-formed documents; follow-up accuracy tuning belongs to the upload harvester's own hardening (KAN-37/KAN-39) if real documents surface problems.
- **Integration with the upload harvester / DB**: out of scope for this story (KAN-37 upload trigger, KAN-39 normalization); `document_parsing` is verified standalone only, with no end-to-end exercise through `ObjectStore` or the `chunks` table.
