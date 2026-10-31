# Capability: document parsing

### Requirement: Section-structured extraction
The system SHALL extract text from PDF, DOCX and Markdown documents as an ordered list of sections, each carrying a heading (text and level), body text and order, derived from the document's own structure rather than fixed-size windows.

#### Scenario: parse-markdown-sections
- **Given** a Markdown document with multiple `#`/`##` headings
- **When** it is parsed
- **Then** the result has one section per heading, in document order, each with the heading text, heading level and the body text that follows it up to the next heading

#### Scenario: parse-docx-sections
- **Given** a DOCX document using "Heading 1"/"Heading 2" paragraph styles to separate topics
- **When** it is parsed
- **Then** the result has one section per heading paragraph, in document order, each with the heading text, heading level and the body paragraphs that follow it up to the next heading

#### Scenario: parse-pdf-sections
- **Given** a PDF document whose headings are visually distinguished (larger or bold font) from body text
- **When** it is parsed
- **Then** the result has one section per detected heading, in document order, each with the heading text and the body text that follows it up to the next heading

### Requirement: Fallback for documents without detected headings
The system SHALL return a single untitled section containing the full extracted text when a document has no detected heading structure.

#### Scenario: parse-no-headings-fallback
- **Given** a document (any of PDF, DOCX, Markdown) with no headings
- **When** it is parsed
- **Then** the result is a single section with an empty/`None` heading and the document's full text as body

### Requirement: Format dispatch by extension
The system SHALL select the correct parser for a document based on its file extension and SHALL reject unsupported extensions with a clear error.

#### Scenario: parse-dispatch-by-extension
- **Given** files named `report.pdf`, `notes.docx` and `readme.md`
- **When** each is passed to the dispatcher
- **Then** each is routed to its matching parser and returns sections; a file named `data.xlsx` raises an explicit "unsupported format" error

### Requirement: Idempotent parsing
Parsing the same document twice SHALL produce the same sections.

#### Scenario: parse-idempotent
- **Given** a fixture document
- **When** it is parsed twice
- **Then** both results are equal (same headings, levels, body text and order)
