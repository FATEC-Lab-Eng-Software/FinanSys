from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdminClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    created_at: datetime
    last_access_at: datetime | None


class AdminClientStatusUpdate(BaseModel):
    is_active: bool


class AdminClientListResponse(BaseModel):
    items: list[AdminClientResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    has_more: bool
