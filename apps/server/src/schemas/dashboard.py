from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DashboardSummary(BaseModel):
    balance: Decimal
    month_inflow: Decimal
    month_outflow: Decimal
    month_net: Decimal


class DashboardGoalItem(BaseModel):
    id: int
    name: str
    accumulated_value: Decimal
    target_value: Decimal
    percentage: Decimal


class DashboardGoals(BaseModel):
    total: int
    done: int
    pending: int
    total_accumulated: Decimal
    total_target: Decimal
    in_progress: list[DashboardGoalItem]


class DashboardCategoryExpense(BaseModel):
    category: str
    total: Decimal


class DashboardTransaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    category: str
    transaction_date: date
    value: Decimal
    source_money: str


class DashboardResponse(BaseModel):
    month_start: date
    summary: DashboardSummary
    goals: DashboardGoals
    expenses_by_category: list[DashboardCategoryExpense]
    recent_transactions: list[DashboardTransaction]