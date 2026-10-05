from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.models.goal import GoalCategory, GoalStatus

NON_NULLABLE_UPDATE_FIELDS = ("name", "category", "target_value", "accumulated_value")


def _clean_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("O nome da meta é obrigatório")
    return value


class GoalCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(min_length=1, max_length=100)
    category: GoalCategory
    target_date: date | None = None
    target_value: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    accumulated_value: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _clean_name(value)


class GoalUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: GoalCategory | None = None
    target_date: date | None = None
    target_value: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    accumulated_value: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _clean_name(value)

    @model_validator(mode="after")
    def validate_changes(self) -> "GoalUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar")
        null_fields = sorted(
            name
            for name in NON_NULLABLE_UPDATE_FIELDS
            if name in self.model_fields_set and getattr(self, name) is None
        )
        if null_fields:
            raise ValueError(f"Campos não podem ser nulos: {', '.join(null_fields)}")
        return self


class GoalFilters(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status: GoalStatus | None = None
    category: GoalCategory | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: GoalCategory
    target_date: date | None
    target_value: Decimal
    accumulated_value: Decimal
    status: GoalStatus
    created_at: datetime
    updated_at: datetime


class GoalProgressResponse(BaseModel):
    goal_id: int
    remaining_value: Decimal
    remaining_percentage: Decimal