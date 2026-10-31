import re

from document_parsing.models import Section

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def parse_markdown(text: str) -> list[Section]:
    """Split Markdown text into sections on ATX (`#`) headings.

    Falls back to a single untitled section when no heading is found.
    """
    lines = text.splitlines()
    heading_indexes = [i for i, line in enumerate(lines) if _HEADING_RE.match(line)]

    if not heading_indexes:
        body = text.strip()
        return [Section(heading=None, level=None, text=body, order=0)]

    sections: list[Section] = []
    for order, start in enumerate(heading_indexes):
        match = _HEADING_RE.match(lines[start])
        assert match is not None
        level = len(match.group(1))
        heading = match.group(2)
        end = heading_indexes[order + 1] if order + 1 < len(heading_indexes) else len(lines)
        body = "\n".join(lines[start + 1 : end]).strip()
        sections.append(Section(heading=heading, level=level, text=body, order=order))

    return sections
