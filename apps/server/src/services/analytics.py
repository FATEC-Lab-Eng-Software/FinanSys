from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.repositories.analytics_repository import AnalyticsRepository
from src.schemas.analytics_schemas import (
    AnalyticsFilters,
    AnalyticsResponse,
    CategoryAnalytics,
    MonthlyAnalytics,
)


class AnalyticsUnavailable(Exception):
    pass


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._analytics = AnalyticsRepository(session)

    def summarize(self, user_id: str, filters: AnalyticsFilters) -> AnalyticsResponse:
        try:
            monthly_rows = self._analytics.monthly_totals(
                user_id=UUID(user_id),
                start_date=filters.start_date,
                end_date=filters.end_date,
            )
            category_rows = self._analytics.expenses_by_category(
                user_id=UUID(user_id),
                start_date=filters.start_date,
                end_date=filters.end_date,
            )
        except SQLAlchemyError:
            self._session.rollback()
            raise AnalyticsUnavailable from None

        month_values = {
            (year, month): {"inflow": Decimal("0.00"), "outflow": Decimal("0.00")}
            for year, month in self._months(filters.start_date, filters.end_date)
        }
        for month, transaction_type, total in monthly_rows:
            month_values[(month.year, month.month)][transaction_type] = total

        monthly = [
            MonthlyAnalytics(
                month=date(year, month, 1),
                inflow=values["inflow"],
                outflow=values["outflow"],
                net_balance=values["inflow"] - values["outflow"],
            )
            for (year, month), values in month_values.items()
        ]
        total_inflow = sum((item.inflow for item in monthly), Decimal("0.00"))
        total_outflow = sum((item.outflow for item in monthly), Decimal("0.00"))

        return AnalyticsResponse(
            start_date=filters.start_date,
            end_date=filters.end_date,
            total_inflow=total_inflow,
            total_outflow=total_outflow,
            net_balance=total_inflow - total_outflow,
            monthly=monthly,
            expenses_by_category=[
                CategoryAnalytics(category=category, total=total)
                for category, total in category_rows
            ],
        )

    @staticmethod
    def _months(start_date: date, end_date: date) -> list[tuple[int, int]]:
        year, month = start_date.year, start_date.month
        months = []
        while (year, month) <= (end_date.year, end_date.month):
            months.append((year, month))
            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1
        return months
