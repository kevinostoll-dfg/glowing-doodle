"""Playbook schemas."""

from datetime import datetime

from pydantic import BaseModel


class RubricCategory(BaseModel):
    """A single rubric category for call scoring."""

    name: str
    description: str
    weight: float
    criteria: list[str]


class PlaybookCreate(BaseModel):
    """Schema for creating a playbook."""

    name: str
    criteria: list[RubricCategory]
    script_template: str | None = None


class PlaybookResponse(BaseModel):
    """Schema for playbook response."""

    id: int
    name: str
    version: int
    is_active: bool
    criteria: list[RubricCategory]
    script_template: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
