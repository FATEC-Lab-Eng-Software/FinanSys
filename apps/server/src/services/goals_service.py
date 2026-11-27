from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models.goal import Goal, GoalStatus
from src.repositories.goals_history_repository import GoalHistoryRepository
from src.repositories.goals_repository import GoalRepository
from src.schemas.goals_schemas import (
    GoalCreate,
    GoalFilters,
    GoalHistoryFilters,
    GoalHistoryResponse,
    GoalHistoryUpdate,
    GoalProgressResponse,
    GoalResponse,
    GoalUpdate,
)
from src.services.notifications_service import NotificationService

import logging

CENTS = Decimal("0.01")

logger = logging.getLogger(__name__)


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
        self._history = GoalHistoryRepository(session)

    def create(self, user_id: str, payload: GoalCreate) -> GoalResponse:
        values = payload.model_dump()
        values["status"] = self._resolve_status(values["target_value"], values["accumulated_value"])
        try:
            if values["status"] == GoalStatus.DONE.value:
                self._stage_goal_completed(user_id, values["name"])
            goal = self._goals.create(user_id=UUID(user_id), values=values)
            if goal.accumulated_value > 0:
                self._history.add(goal_id=goal.id, value=goal.accumulated_value)
            self._session.commit()
            self._session.refresh(goal)
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
        goal = self._find(user_id, goal_id, for_update=True)
        values = payload.model_dump(exclude_unset=True)
        new_balance = values.get("accumulated_value", goal.accumulated_value)
        delta = new_balance - goal.accumulated_value
        was_done = goal.status == GoalStatus.DONE.value
        values["status"] = self._resolve_status(
            values.get("target_value", goal.target_value), new_balance
        )
        try:
            if not was_done and values["status"] == GoalStatus.DONE.value:
                self._stage_goal_completed(user_id, values.get("name", goal.name))
            self._goals.update(goal, values=values)
            if delta != 0:
                self._history.add(goal_id=goal.id, value=delta)
            self._session.commit()
            self._session.refresh(goal)
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return GoalResponse.model_validate(goal)

    def delete(self, user_id: str, goal_id: int) -> None:
        goal = self._find(user_id, goal_id)
        try:
            self._goals.delete(goal)
            self._session.commit()
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

    def list_history(
        self, user_id: str, goal_id: int, filters: GoalHistoryFilters
    ) -> list[GoalHistoryResponse]:
        goal = self._find(user_id, goal_id)
        try:
            entries = self._history.list_by_goal(goal_id=goal.id, filters=filters)
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return [GoalHistoryResponse.model_validate(entry) for entry in entries]

    def edit_history_entry(
        self, user_id: str, goal_id: int, history_id: int, payload: GoalHistoryUpdate
    ) -> GoalHistoryResponse:
        goal = self._find(user_id, goal_id, for_update=True)
        try:
            entry = self._history.get(goal_id=goal.id, history_id=history_id)
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        if entry is None:
            raise GoalFailure(404, "goal_history_not_found", "Registro não encontrado.")

        new_balance = goal.accumulated_value + payload.value - entry.value
        if new_balance < 0:
            raise GoalFailure(422, "negative_balance", "O saldo da meta não pode ficar negativo.")

        try:
            entry.value = payload.value
            if goal.status != GoalStatus.DONE.value and new_balance >= goal.target_value:
                self._stage_goal_completed(user_id, goal.name)
            self._goals.update(
                goal,
                values={
                    "accumulated_value": new_balance,
                    "status": self._resolve_status(goal.target_value, new_balance),
                },
            )
            self._session.commit()
            self._session.refresh(entry)
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return GoalHistoryResponse.model_validate(entry)

    def _find(self, user_id: str, goal_id: int, *, for_update: bool = False) -> Goal:
        try:
            goal = self._goals.get_for_user(
                goal_id=goal_id, user_id=UUID(user_id), for_update=for_update
            )
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        if goal is None:
            raise GoalFailure(404, "goal_not_found", "Meta não encontrada.")
        return goal

    def _resolve_status(self, target_value: Decimal, accumulated_value: Decimal) -> str:
        if accumulated_value >= target_value:
            return GoalStatus.DONE.value
        return GoalStatus.PENDING.value

    def _stage_goal_completed(self, user_id: str, goal_name: str) -> None:
        NotificationService(self._session).stage(
            user_id,
            category="goal",
            title="Meta concluída",
            description=f"Parabéns! Você concluiu a meta {goal_name}.",
        )

    def _store_unavailable(self) -> GoalFailure:
        logger.exception("goal store error")
        self._session.rollback()
        return GoalFailure(
            503,
            "goal_store_unavailable",
            "Não foi possível acessar as metas.",
        )
