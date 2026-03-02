"""Shop schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ShopCreate(BaseModel):
    """Schema for creating a shop."""

    name: str
    shop_code: str
    phone_number: str | None = None
    timezone: str = "America/New_York"
    business_hours: dict[str, Any] = {}
    address: str | None = None


class ShopUpdate(BaseModel):
    """Schema for updating a shop."""

    name: str | None = None
    phone_number: str | None = None
    timezone: str | None = None
    business_hours: dict[str, Any] | None = None
    address: str | None = None


class ShopResponse(BaseModel):
    """Schema for shop response."""

    id: int
    name: str
    shop_code: str
    phone_number: str | None
    timezone: str
    business_hours: dict[str, Any]
    address: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
