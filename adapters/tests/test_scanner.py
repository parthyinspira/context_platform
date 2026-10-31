"""Tests for the secret/PII scanner (KAN-82).

All secret-like values below are seeded fixtures, deliberately fake and
clearly non-real (an obviously-fake AWS access key id, a placeholder token,
a placeholder password, a placeholder PEM block). None of them are real
credentials.
"""
from adapters.scanning.scanner import scan_and_redact

FAKE_AWS_KEY = "AKIAFAKEEXAMPLE12345"  # seeded fixture, not a real AWS key (AKIA + 16 chars)
FAKE_API_TOKEN = "api_key: 'fake-ztoken-abcdefghijklmnop0987654321'"  # seeded fixture
FAKE_PASSWORD = "password = 'hunter2fakepassword'"  # seeded fixture
FAKE_PRIVATE_KEY = (
    "-----BEGIN RSA PRIVATE KEY-----\n"
    "ZmFrZS1wcml2YXRlLWtleS1maXh0dXJlLW5vdC1yZWFs\n"
    "-----END RSA PRIVATE KEY-----"
)
FAKE_CONN_STRING = "postgres://dbuser:fakeSecretPass123@db.example.com:5432/app"
FAKE_EMAIL = "jane.doe@example.com"
FAKE_SSN = "123-45-6789"
FAKE_CREDIT_CARD = "4111 1111 1111 1111"  # seeded fixture, a well-known test-only card number


def test_detects_and_redacts_aws_key() -> None:
    result = scan_and_redact(f"config contains {FAKE_AWS_KEY} in plaintext")

    assert FAKE_AWS_KEY not in result.redacted_text
    assert any(f.kind == "aws_access_key_id" and f.category == "secret" for f in result.findings)
    assert result.sensitivity == "restricted"


def test_detects_and_redacts_generic_api_token() -> None:
    result = scan_and_redact(FAKE_API_TOKEN)

    assert "fake-ztoken-abcdefghijklmnop0987654321" not in result.redacted_text
    assert any(f.category == "secret" for f in result.findings)
    assert result.sensitivity == "restricted"


def test_detects_and_redacts_password_assignment() -> None:
    result = scan_and_redact(FAKE_PASSWORD)

    assert "hunter2fakepassword" not in result.redacted_text
    assert any(f.kind == "password_assignment" for f in result.findings)
    assert result.sensitivity == "restricted"


def test_detects_and_redacts_private_key_block() -> None:
    result = scan_and_redact(f"see key below\n{FAKE_PRIVATE_KEY}\nend")

    assert "ZmFrZS1wcml2YXRlLWtleS1maXh0dXJlLW5vdC1yZWFs" not in result.redacted_text
    assert any(f.kind == "private_key_block" for f in result.findings)
    assert result.sensitivity == "restricted"


def test_detects_and_redacts_connection_string_password() -> None:
    result = scan_and_redact(FAKE_CONN_STRING)

    assert "fakeSecretPass123" not in result.redacted_text
    assert "dbuser" in result.redacted_text  # username is not a secret, kept
    assert any(f.kind == "connection_string_password" for f in result.findings)
    assert result.sensitivity == "restricted"


def test_detects_multiple_secret_kinds_in_one_text() -> None:
    text = f"{FAKE_AWS_KEY}\n{FAKE_PASSWORD}\n{FAKE_PRIVATE_KEY}"
    result = scan_and_redact(text)

    kinds = {f.kind for f in result.findings}
    assert {"aws_access_key_id", "password_assignment", "private_key_block"} <= kinds
    assert result.sensitivity == "restricted"


def test_pii_detected_without_a_secret_sets_confidential() -> None:
    result = scan_and_redact(f"Contact {FAKE_EMAIL} or SSN {FAKE_SSN} for details.")

    assert FAKE_EMAIL not in result.redacted_text
    assert FAKE_SSN not in result.redacted_text
    assert all(f.category == "pii" for f in result.findings)
    assert result.sensitivity == "confidential"


def test_detects_and_redacts_credit_card_number() -> None:
    result = scan_and_redact(f"Card on file: {FAKE_CREDIT_CARD}")

    assert FAKE_CREDIT_CARD not in result.redacted_text
    assert any(f.kind == "credit_card" and f.category == "pii" for f in result.findings)
    assert result.sensitivity == "confidential"


def test_no_findings_returns_text_unchanged_and_internal_sensitivity() -> None:
    text = "This is a plain README with no secrets or personal data."
    result = scan_and_redact(text)

    assert result.redacted_text == text
    assert result.findings == []
    assert result.sensitivity == "internal"


def test_secret_outranks_pii_for_sensitivity() -> None:
    text = f"{FAKE_AWS_KEY} belongs to {FAKE_EMAIL}"
    result = scan_and_redact(text)

    assert result.sensitivity == "restricted"
    assert result.has_secrets
    assert result.has_pii
