from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.models.transaction import TransactionCategory, TransactionType


class TransactionCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type: TransactionType
    category: TransactionCategory
    transaction_date: date
    value: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    source_money: str = Field(min_length=1, max_length=100)

    @field_validator("source_money")
    @classmethod
    def validate_source_money(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A origem do dinheiro é obrigatória")
        return value


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type: TransactionType | None = None
    category: TransactionCategory | None = None
    transaction_date: date | None = None
    value: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    source_money: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("source_money")
    @classmethod
    def validate_source_money(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("A origem do dinheiro é obrigatória")
        return value

    @model_validator(mode="after")
    def validate_changes(self) -> "TransactionUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar")
        null_fields = sorted(name for name in self.model_fields_set if getattr(self, name) is None)
        if null_fields:
            raise ValueError(f"Campos não podem ser nulos: {', '.join(null_fields)}")
        return self


class TransactionFilters(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    start_date: date | None = None
    end_date: date | None = None
    type: TransactionType | None = None
    category: TransactionCategory | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_period(self) -> "TransactionFilters":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("A data inicial deve ser anterior ou igual à data final")
        return self


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: TransactionType
    category: TransactionCategory
    transaction_date: date
    value: Decimal
    source_money: str
    created_at: datetime
    updated_at: datetime