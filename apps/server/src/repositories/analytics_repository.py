from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from src.models.transaction import Transaction


class AnalyticsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def monthly_totals(
        self, *, user_id: UUID, start_date: date, end_date: date
    ) -> list[tuple[date, str, Decimal]]:
        month = cast(func.date_trunc("month", Transaction.transaction_date), Date)
        statement = (
            select(month, Transaction.type, func.sum(Transaction.value))
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by(month, Transaction.type)
            .order_by(month)
        )
        return [
            (row[0], row[1], row[2] or Decimal("0.00"))
            for row in self._session.execute(statement)
        ]

    def expenses_by_category(
        self, *, user_id: UUID, start_date: date, end_date: date
    ) -> list[tuple[str, Decimal]]:
        statement = (
            select(Transaction.category, func.sum(Transaction.value))
            .where(
                Transaction.user_id == user_id,
                Transaction.type == "outflow",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.value).desc(), Transaction.category)
        )
        return [
            (row[0], row[1] or Decimal("0.00"))
            for row in self._session.execute(statement)
        ]
