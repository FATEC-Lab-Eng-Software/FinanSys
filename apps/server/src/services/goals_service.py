from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models.goal import Goal, GoalStatus
from src.repositories.goals_repository import GoalRepository
from src.schemas.goals_schemas import (
    GoalCreate,
    GoalFilters,
    GoalProgressResponse,
    GoalResponse,
    GoalUpdate,
)

CENTS = Decimal("0.01")


class GoalFailure(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class GoalService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._goals = GoalRepository(session)

    def create(self, user_id: str, payload: GoalCreate) -> GoalResponse:
        values = payload.model_dump()
        values["status"] = self._resolve_status(values["target_value"], values["accumulated_value"])
        try:
            goal = self._goals.create(user_id=UUID(user_id), values=values)
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return GoalResponse.model_validate(goal)

    def list_for_user(self, user_id: str, filters: GoalFilters) -> list[GoalResponse]:
        try:
            goals = self._goals.list_for_user(user_id=UUID(user_id), filters=filters)
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return [GoalResponse.model_validate(goal) for goal in goals]

    def get(self, user_id: str, goal_id: int) -> GoalResponse:
        return GoalResponse.model_validate(self._find(user_id, goal_id))

    def update(self, user_id: str, goal_id: int, payload: GoalUpdate) -> GoalResponse:
        goal = self._find(user_id, goal_id)
        values = payload.model_dump(exclude_unset=True)
        values["status"] = self._resolve_status(
            values.get("target_value", goal.target_value),
            values.get("accumulated_value", goal.accumulated_value),
        )
        try:
            goal = self._goals.update(goal, values=values)
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return GoalResponse.model_validate(goal)

    def delete(self, user_id: str, goal_id: int) -> None:
        goal = self._find(user_id, goal_id)
        try:
            self._goals.delete(goal)
        except SQLAlchemyError:
            raise self._store_unavailable() from None

    def get_progress(self, user_id: str, goal_id: int) -> GoalProgressResponse:
        goal = self._find(user_id, goal_id)
        remaining_value = max(goal.target_value - goal.accumulated_value, Decimal("0")).quantize(CENTS)
        remaining_percentage = (remaining_value / goal.target_value * 100).quantize(
            CENTS,
            rounding=ROUND_HALF_UP,
        )
        return GoalProgressResponse(
            goal_id=goal.id,
            remaining_value=remaining_value,
            remaining_percentage=remaining_percentage,
        )

    def _find(self, user_id: str, goal_id: int) -> Goal:
        try:
            goal = self._goals.get_for_user(goal_id=goal_id, user_id=UUID(user_id))
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        if goal is None:
            raise GoalFailure(404, "goal_not_found", "Meta não encontrada.")
        return goal

    def _resolve_status(self, target_value: Decimal, accumulated_value: Decimal) -> str:
        if accumulated_value >= target_value:
            return GoalStatus.DONE.value
        return GoalStatus.PENDING.value

    def _store_unavailable(self) -> GoalFailure:
        self._session.rollback()
        return GoalFailure(
            503,
            "goal_store_unavailable",
            "Não foi possível acessar as metas.",
        )