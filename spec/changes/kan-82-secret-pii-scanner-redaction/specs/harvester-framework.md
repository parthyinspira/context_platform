# Delta for harvester framework

## MODIFIED Requirements
### Requirement: Read-only and secret-safe
A harvester SHALL use read-only credentials and SHALL redact detected secrets before storage, using the shared scanner (`adapters.scanning.scan_and_redact`), which also detects common PII and derives a `sensitivity` level. (was: stated the rule with no implementation referenced)

#### Scenario: secret in a file
- **Given** a file containing an API key
- **When** it is harvested
- **Then** the key is redacted in stored text and the object is marked sensitive

#### Scenario: AWS key, token, password, private key detected
- **Given** text containing a seeded AWS-shaped access key, a generic API token, a password assignment, and a PEM private key block
- **When** the text is scanned
- **Then** each is detected and replaced with a redaction marker in the returned text, and none of the original secret values appear in the output

#### Scenario: PII detected without a secret
- **Given** text containing only an email address or an SSN-shaped number, with no secret pattern present
- **When** the text is scanned
- **Then** the PII is redacted and the derived sensitivity is `confidential`, not `restricted`

#### Scenario: no findings
- **Given** text containing no secret or PII pattern
- **When** the text is scanned
- **Then** the text is returned unchanged and the derived sensitivity is `internal`

#### Scenario: redaction before storage
- **Given** text containing a seeded secret
- **When** `PostgresChunkWriter.write()` is called with that text
- **Then** the row inserted into `chunks.text` contains the redaction marker, never the raw secret value, and `chunks.metadata` records `sensitivity: "restricted"`
