from datetime import date
from decimal import Decimal

from pydantic import BaseModel, model_validator

from src.models.transaction import TransactionCategory


class AnalyticsFilters(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_period(self) -> "AnalyticsFilters":
        if self.start_date > self.end_date:
            raise ValueError("A data inicial deve ser anterior ou igual à data final")
        month_count = (self.end_date.year - self.start_date.year) * 12
        month_count += self.end_date.month - self.start_date.month + 1
        if month_count > 120:
            raise ValueError("O período máximo para análise é de 120 meses.")
        return self


class MonthlyAnalytics(BaseModel):
    month: date
    inflow: Decimal
    outflow: Decimal
    net_balance: Decimal


class CategoryAnalytics(BaseModel):
    category: TransactionCategory
    total: Decimal


class AnalyticsResponse(BaseModel):
    start_date: date
    end_date: date
    total_inflow: Decimal
    total_outflow: Decimal
    net_balance: Decimal
    monthly: list[MonthlyAnalytics]
    expenses_by_category: list[CategoryAnalytics]
