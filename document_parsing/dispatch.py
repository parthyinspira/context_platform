from pathlib import Path

from document_parsing.docx_parser import parse_docx
from document_parsing.markdown_parser import parse_markdown
from document_parsing.models import Section
from document_parsing.pdf_parser import parse_pdf

_PARSERS_BY_EXTENSION = {
    ".md": "markdown",
    ".docx": "docx",
    ".pdf": "pdf",
}


def parse_document(data: bytes, filename: str) -> list[Section]:
    """Parse `data` into sections, choosing the parser from `filename`'s extension.

    Raises `ValueError` for an extension with no registered parser.
    """
    extension = Path(filename).suffix.lower()
    kind = _PARSERS_BY_EXTENSION.get(extension)

    if kind == "markdown":
        return parse_markdown(data.decode("utf-8"))
    if kind == "docx":
        return parse_docx(data)
    if kind == "pdf":
        return parse_pdf(data)

    raise ValueError(f"unsupported document format: {extension!r}")
