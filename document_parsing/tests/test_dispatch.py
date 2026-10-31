import pytest

from document_parsing.dispatch import parse_document
from document_parsing.tests.test_docx_parser import MULTI_HEADING_DOCX
from document_parsing.tests.test_pdf_parser import MULTI_HEADING_PDF

MARKDOWN_BYTES = b"# Title\n\nBody text.\n"


def test_parse_document_routes_markdown():
    sections = parse_document(MARKDOWN_BYTES, "readme.md")
    assert sections[0].heading == "Title"


def test_parse_document_routes_docx():
    sections = parse_document(MULTI_HEADING_DOCX, "notes.docx")
    assert sections[0].heading == "Title"


def test_parse_document_routes_pdf():
    sections = parse_document(MULTI_HEADING_PDF, "report.pdf")
    assert sections[0].heading == "Title"


def test_parse_document_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="unsupported"):
        parse_document(b"irrelevant", "data.xlsx")
