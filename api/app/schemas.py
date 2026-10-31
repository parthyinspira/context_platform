"""Request/response models for the source registry API."""
import re

from pydantic import BaseModel, field_validator

SENSITIVITY_LEVELS = {"public", "internal", "confidential", "restricted"}

# A pragmatic 5-field cron check: each field is `*`, a number, a range, a step or a
# comma-separated list of those. This intentionally does not validate field *ranges*
# (e.g. month 1-12) — it rejects obviously malformed schedules without a heavy
# dependency, per CLAUDE.md's "small modules" convention.
_CRON_FIELD = r"(\*|[0-9]+)(-[0-9]+)?(/[0-9]+)?(,(\*|[0-9]+)(-[0-9]+)?(/[0-9]+)?)*"
_CRON_RE = re.compile(rf"^{_CRON_FIELD}(\s+{_CRON_FIELD}){{4}}$")


def is_valid_cron(value: str) -> bool:
    return bool(_CRON_RE.match(value.strip()))


class SourceCreate(BaseModel):
    type: str
    uri: str
    schedule: str
    credentials_ref: str
    owner: str
    sensitivity: str

    @field_validator("type", "uri", "credentials_ref", "owner")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("schedule")
    @classmethod
    def valid_cron(cls, value: str) -> str:
        if not value or not is_valid_cron(value):
            raise ValueError("schedule must be a valid 5-field cron expression")
        return value

    @field_validator("sensitivity")
    @classmethod
    def valid_sensitivity(cls, value: str) -> str:
        if value not in SENSITIVITY_LEVELS:
            raise ValueError(f"sensitivity must be one of {sorted(SENSITIVITY_LEVELS)}")
        return value


class SourceOut(BaseModel):
    id: str
    type: str
    uri: str
    schedule: str
    credentials_ref: str
    owner: str
    sensitivity: str
    status: str
