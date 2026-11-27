from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GoalHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    goal_id: int
    value: Decimal
    created_at: datetime


class GoalHistoryFilters(BaseModel):
    start: datetime | None = None
    end: datetime | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class GoalHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    goal_id: int
    value: Decimal
    created_at: datetime


class GoalHistoryUpdate(BaseModel):
    value: Decimal = Field(max_digits=12, decimal_places=2)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: Decimal) -> Decimal:
        if value == 0:
            raise ValueError("O valor do registro não pode ser zero")
        return value
