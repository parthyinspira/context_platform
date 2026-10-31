import io

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from document_parsing.pdf_parser import parse_pdf


def _build_pdf(add_headings: bool) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    y = 720

    def line(text: str, size: float, bold: bool = False) -> None:
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(72, y, text)
        y -= size + 10

    if add_headings:
        line("Title", 20, bold=True)
        line("Intro text.", 11)
        line("Section One", 16, bold=True)
        line("Body of section one.", 11)
        line("More text.", 11)
        line("Section Two", 16, bold=True)
        line("Body of section two.", 11)
    else:
        line("Just a paragraph of text.", 11)
        line("Another paragraph, no headings at all.", 11)

    c.showPage()
    c.save()
    return buf.getvalue()


MULTI_HEADING_PDF = _build_pdf(add_headings=True)
NO_HEADINGS_PDF = _build_pdf(add_headings=False)


def test_parse_pdf_sections():
    sections = parse_pdf(MULTI_HEADING_PDF)

    assert [s.heading for s in sections] == ["Title", "Section One", "Section Two"]
    assert sections[0].level == 1
    assert sections[1].level == sections[2].level == 2
    assert [s.order for s in sections] == [0, 1, 2]
    assert "Intro text." in sections[0].text
    assert "Body of section one." in sections[1].text
    assert "More text." in sections[1].text
    assert "Body of section two." in sections[2].text


def test_parse_pdf_no_headings_fallback():
    sections = parse_pdf(NO_HEADINGS_PDF)

    assert len(sections) == 1
    assert sections[0].heading is None
    assert sections[0].level is None
    assert "Just a paragraph of text." in sections[0].text
    assert "Another paragraph, no headings at all." in sections[0].text


def test_parse_pdf_idempotent():
    assert parse_pdf(MULTI_HEADING_PDF) == parse_pdf(MULTI_HEADING_PDF)
