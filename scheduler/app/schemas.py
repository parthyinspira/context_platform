"""Request/response models for the dispatcher (scheduler) API."""
from pydantic import BaseModel


class RunOut(BaseModel):
    id: str
    source_id: str
    status: str


class DueSourceOut(BaseModel):
    id: str
    type: str
    uri: str
    last_harvest_at: str | None
