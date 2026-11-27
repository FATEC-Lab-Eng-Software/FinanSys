from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models.goal import Goal, GoalStatus
from src.models.transaction import Transaction
from src.schemas.dashboard import (
    DashboardCategoryExpense,
    DashboardGoalItem,
    DashboardGoals,
    DashboardResponse,
    DashboardSummary,
    DashboardTransaction,
)

ZERO = Decimal("0.00")
CENTS = Decimal("0.01")
IN_PROGRESS_LIMIT = 3
CATEGORY_LIMIT = 5
RECENT_LIMIT = 5


class DashboardFailure(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class DashboardService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: str) -> DashboardResponse:
        owner = UUID(user_id)
        month_start = date.today().replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        try:
            return DashboardResponse(
                month_start=month_start,
                summary=self._summary(owner, month_start, next_month),
                goals=self._goals_overview(owner),
                expenses_by_category=self._expenses_by_category(owner, month_start, next_month),
                recent_transactions=self._recent_transactions(owner),
            )
        except SQLAlchemyError:
            self._session.rollback()
            raise DashboardFailure(
                503,
                "dashboard_unavailable",
                "Não foi possível carregar o dashboard.",
            ) from None

    def _totals_by_type(
        self, owner: UUID, start: date | None = None, end: date | None = None
    ) -> dict[str, Decimal]:
        statement = select(
            Transaction.type, func.coalesce(func.sum(Transaction.value), 0)
        ).where(Transaction.user_id == owner)
        if start is not None:
            statement = statement.where(Transaction.transaction_date >= start)
        if end is not None:
            statement = statement.where(Transaction.transaction_date < end)
        statement = statement.group_by(Transaction.type)
        return {tx_type: Decimal(total) for tx_type, total in self._session.execute(statement)}

    def _summary(self, owner: UUID, month_start: date, next_month: date) -> DashboardSummary:
        overall = self._totals_by_type(owner)
        month = self._totals_by_type(owner, month_start, next_month)
        month_inflow = month.get("inflow", ZERO)
        month_outflow = month.get("outflow", ZERO)
        return DashboardSummary(
            balance=overall.get("inflow", ZERO) - overall.get("outflow", ZERO),
            month_inflow=month_inflow,
            month_outflow=month_outflow,
            month_net=month_inflow - month_outflow,
        )

    def _goals_overview(self, owner: UUID) -> DashboardGoals:
        goals = list(self._session.scalars(select(Goal).where(Goal.user_id == owner)))
        done = [goal for goal in goals if goal.status == GoalStatus.DONE.value]
        pending = [goal for goal in goals if goal.status != GoalStatus.DONE.value]
        in_progress = sorted(
            pending,
            key=lambda goal: goal.accumulated_value / goal.target_value,
            reverse=True,
        )[:IN_PROGRESS_LIMIT]

        return DashboardGoals(
            total=len(goals),
            done=len(done),
            pending=len(pending),
            total_accumulated=sum((goal.accumulated_value for goal in goals), ZERO),
            total_target=sum((goal.target_value for goal in goals), ZERO),
            in_progress=[
                DashboardGoalItem(
                    id=goal.id,
                    name=goal.name,
                    accumulated_value=goal.accumulated_value,
                    target_value=goal.target_value,
                    percentage=self._percentage(goal.accumulated_value, goal.target_value),
                )
                for goal in in_progress
            ],
        )

    def _expenses_by_category(
        self, owner: UUID, month_start: date, next_month: date
    ) -> list[DashboardCategoryExpense]:
        total = func.sum(Transaction.value)
        statement = (
            select(Transaction.category, total)
            .where(
                Transaction.user_id == owner,
                Transaction.type == "outflow",
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < next_month,
            )
            .group_by(Transaction.category)
            .order_by(total.desc())
            .limit(CATEGORY_LIMIT)
        )
        return [
            DashboardCategoryExpense(category=category, total=Decimal(value))
            for category, value in self._session.execute(statement)
        ]

    def _recent_transactions(self, owner: UUID) -> list[DashboardTransaction]:
        statement = (
            select(Transaction)
            .where(Transaction.user_id == owner)
            .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            .limit(RECENT_LIMIT)
        )
        return [
            DashboardTransaction.model_validate(item)
            for item in self._session.scalars(statement)
        ]

    @staticmethod
    def _percentage(accumulated: Decimal, target: Decimal) -> Decimal:
        return min(accumulated / target * 100, Decimal(100)).quantize(CENTS, rounding=ROUND_HALF_UP)