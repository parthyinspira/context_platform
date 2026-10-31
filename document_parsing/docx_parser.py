import io
import re

from docx import Document

from document_parsing.models import Section

_HEADING_STYLE_RE = re.compile(r"^Heading\s+(\d+)$", re.IGNORECASE)


def parse_docx(data: bytes) -> list[Section]:
    """Split a DOCX document into sections on "Heading N" paragraph styles.

    Falls back to a single untitled section when no heading style is used.
    """
    doc = Document(io.BytesIO(data))
    paragraphs = [
        (p.text, _heading_level(p.style.name if p.style else None)) for p in doc.paragraphs
    ]

    heading_indexes = [i for i, (_, level) in enumerate(paragraphs) if level is not None]

    if not heading_indexes:
        body = "\n".join(text for text, _ in paragraphs if text.strip()).strip()
        return [Section(heading=None, level=None, text=body, order=0)]

    sections: list[Section] = []
    for order, start in enumerate(heading_indexes):
        heading_text, level = paragraphs[start]
        end = heading_indexes[order + 1] if order + 1 < len(heading_indexes) else len(paragraphs)
        body_paragraphs = [text for text, _ in paragraphs[start + 1 : end] if text.strip()]
        sections.append(
            Section(heading=heading_text, level=level, text="\n".join(body_paragraphs), order=order)
        )

    return sections


def _heading_level(style_name: str | None) -> int | None:
    if not style_name:
        return None
    match = _HEADING_STYLE_RE.match(style_name.strip())
    return int(match.group(1)) if match else None
