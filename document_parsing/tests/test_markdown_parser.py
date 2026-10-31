from document_parsing.markdown_parser import parse_markdown

MULTI_HEADING = """# Title

Intro text.

## Section One

Body of section one.
More text.

## Section Two

Body of section two.

### Nested Section

Nested body.
"""

NO_HEADINGS = "Just a paragraph of text.\n\nAnother paragraph, no headings at all.\n"


def test_parse_markdown_sections():
    sections = parse_markdown(MULTI_HEADING)

    assert [s.heading for s in sections] == [
        "Title",
        "Section One",
        "Section Two",
        "Nested Section",
    ]
    assert [s.level for s in sections] == [1, 2, 2, 3]
    assert [s.order for s in sections] == [0, 1, 2, 3]
    assert "Intro text." in sections[0].text
    assert "Body of section one." in sections[1].text
    assert "More text." in sections[1].text
    assert "Body of section two." in sections[2].text
    assert "Nested body." in sections[3].text


def test_parse_markdown_no_headings_fallback():
    sections = parse_markdown(NO_HEADINGS)

    assert len(sections) == 1
    assert sections[0].heading is None
    assert sections[0].level is None
    assert sections[0].order == 0
    assert "Just a paragraph of text." in sections[0].text
    assert "Another paragraph, no headings at all." in sections[0].text


def test_parse_markdown_idempotent():
    assert parse_markdown(MULTI_HEADING) == parse_markdown(MULTI_HEADING)
