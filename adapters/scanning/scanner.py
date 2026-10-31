"""Secret and PII scanner with redaction (KAN-82).

Deterministic, regex-based detection of common secrets (keys, tokens,
passwords, private keys) and common PII in fetched text, matching
`docs/HARVESTERS.md` rule 8 ("Secrets and PII") and the "Read-only and
secret-safe" requirement in `spec/capabilities/harvester-framework.md`.

Pure function, no I/O, no network calls, no LLM, no cloud SDK imports.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_REDACTED = "[REDACTED:{kind}]"

# (kind, category, pattern, group)
# group is the regex group whose span gets replaced; 0 means the whole match.
_PATTERNS: list[tuple[str, str, re.Pattern[str], int]] = [
    (
        "private_key_block",
        "secret",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
            r"[\s\S]+?"
            r"-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
        ),
        0,
    ),
    ("aws_access_key_id", "secret", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 0),
    (
        "slack_token",
        "secret",
        re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
        0,
    ),
    (
        "github_token",
        "secret",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
        0,
    ),
    (
        "connection_string_password",
        "secret",
        re.compile(r"(?i)([a-z][a-z0-9+.\-]*://[^:/\s@]+:)([^@/\s]+)(@)"),
        2,
    ),
    (
        "generic_api_key",
        "secret",
        re.compile(
            r"(?i)\b(?:api[_-]?key|api[_-]?token|access[_-]?token|"
            r"secret[_-]?key|client[_-]?secret)\b\s*[:=]\s*['\"]?"
            r"([A-Za-z0-9\-_.]{12,})['\"]?"
        ),
        1,
    ),
    (
        "bearer_token",
        "secret",
        re.compile(r"(?i)\bBearer\s+([A-Za-z0-9\-_.=]{10,})"),
        1,
    ),
    (
        "password_assignment",
        "secret",
        re.compile(
            r"(?i)\b(?:password|passwd|pwd)\b\s*[:=]\s*['\"]?"
            r"([^\s'\"]{6,})['\"]?"
        ),
        1,
    ),
    ("email", "pii", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), 0),
    ("ssn", "pii", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), 0),
    # Credit-card-shaped number: 13-16 digits, optionally grouped with spaces or
    # dashes. Intentionally broad (flagged in proposal.md as a known
    # false-positive risk) — it only affects redaction/sensitivity, which is
    # the safe direction to err in.
    (
        "credit_card",
        "pii",
        re.compile(r"\b(?:\d[ -]?){12,15}\d\b"),
        0,
    ),
]


@dataclass(frozen=True)
class Finding:
    kind: str
    category: str  # "secret" or "pii"


@dataclass(frozen=True)
class ScanResult:
    redacted_text: str
    findings: list[Finding] = field(default_factory=list)
    sensitivity: str = "internal"

    @property
    def has_secrets(self) -> bool:
        return any(f.category == "secret" for f in self.findings)

    @property
    def has_pii(self) -> bool:
        return any(f.category == "pii" for f in self.findings)


def _apply_pattern(
    text: str,
    kind: str,
    category: str,
    pattern: re.Pattern[str],
    group: int,
    findings: list[Finding],
) -> str:
    out: list[str] = []
    last_end = 0
    for match in pattern.finditer(text):
        start, end = match.span(group)
        if start < 0:
            continue
        out.append(text[last_end:start])
        out.append(_REDACTED.format(kind=kind))
        findings.append(Finding(kind=kind, category=category))
        last_end = end
    out.append(text[last_end:])
    return "".join(out)


def _derive_sensitivity(findings: list[Finding]) -> str:
    if any(f.category == "secret" for f in findings):
        return "restricted"
    if any(f.category == "pii" for f in findings):
        return "confidential"
    return "internal"


def scan_and_redact(text: str) -> ScanResult:
    """Scan `text` for secrets and PII, redact matches, and derive a sensitivity.

    Patterns are applied in order (private key blocks and well-formed tokens
    first, broader password/PII patterns last) so earlier redactions don't
    get re-matched by broader patterns running afterwards.
    """
    findings: list[Finding] = []
    redacted = text
    for kind, category, pattern, group in _PATTERNS:
        redacted = _apply_pattern(redacted, kind, category, pattern, group, findings)
    return ScanResult(
        redacted_text=redacted,
        findings=findings,
        sensitivity=_derive_sensitivity(findings),
    )
