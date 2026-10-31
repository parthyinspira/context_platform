import io
from dataclasses import dataclass

from pypdf import PdfReader

from document_parsing.models import Section

_HEADING_SIZE_RATIO = 1.15


@dataclass
class _Line:
    text: str = ""
    max_size: float = 0.0


def parse_pdf(data: bytes) -> list[Section]:
    """Split a PDF into sections using a font-size heading heuristic.

    Lines whose text is meaningfully larger than the document's most common
    (body) font size are treated as headings. Falls back to a single
    untitled section when no such heading is detected.
    """
    reader = PdfReader(io.BytesIO(data))
    lines = _extract_lines(reader)
    lines = [line for line in lines if line.text.strip()]

    if not lines:
        return [Section(heading=None, level=None, text="", order=0)]

    body_size = _most_common_size(lines)
    heading_indexes = [
        i for i, line in enumerate(lines) if line.max_size >= body_size * _HEADING_SIZE_RATIO
    ]

    if not heading_indexes:
        body = "\n".join(line.text for line in lines).strip()
        return [Section(heading=None, level=None, text=body, order=0)]

    sizes = sorted({lines[i].max_size for i in heading_indexes}, reverse=True)

    sections: list[Section] = []
    for order, start in enumerate(heading_indexes):
        heading_line = lines[start]
        level = sizes.index(heading_line.max_size) + 1
        end = heading_indexes[order + 1] if order + 1 < len(heading_indexes) else len(lines)
        body = "\n".join(line.text for line in lines[start + 1 : end]).strip()
        sections.append(
            Section(heading=heading_line.text.strip(), level=level, text=body, order=order)
        )

    return sections


def _extract_lines(reader: PdfReader) -> list[_Line]:
    lines: list[_Line] = []
    current = _Line()

    def visitor(text: str, cm, tm, font_dict, font_size: float) -> None:
        nonlocal current
        if not text:
            return
        *completed, remainder = text.split("\n")
        for piece in completed:
            current.text += piece
            if piece:
                current.max_size = max(current.max_size, font_size or 0.0)
            if current.text.strip():
                lines.append(current)
            current = _Line()
        current.text += remainder
        if remainder:
            current.max_size = max(current.max_size, font_size or 0.0)

    for page in reader.pages:
        page.extract_text(visitor_text=visitor)
        if current.text.strip():
            lines.append(current)
        current = _Line()

    return lines


def _most_common_size(lines: list[_Line]) -> float:
    counts: dict[float, int] = {}
    for line in lines:
        rounded = round(line.max_size, 1)
        counts[rounded] = counts.get(rounded, 0) + 1
    return max(counts, key=lambda size: counts[size])
