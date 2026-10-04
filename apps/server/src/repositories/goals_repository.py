from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.goal import Goal
from src.schemas.goals_schemas import GoalFilters


class GoalRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, user_id: UUID, values: dict[str, object]) -> Goal:
        goal = Goal(user_id=user_id, **values)
        self._session.add(goal)
        self._session.commit()
        self._session.refresh(goal)
        return goal

    def get_for_user(self, *, goal_id: int, user_id: UUID) -> Goal | None:
        return self._session.scalar(
            select(Goal).where(
                Goal.id == goal_id,
                Goal.user_id == user_id,
            )
        )

    def list_for_user(self, *, user_id: UUID, filters: GoalFilters) -> list[Goal]:
        statement = select(Goal).where(Goal.user_id == user_id)
        if filters.status is not None:
            statement = statement.where(Goal.status == filters.status)
        if filters.category is not None:
            statement = statement.where(Goal.category == filters.category)
        statement = (
            statement.order_by(Goal.created_at.desc(), Goal.id.desc())
            .limit(filters.limit)
            .offset(filters.offset)
        )
        return list(self._session.scalars(statement))

    def update(self, goal: Goal, *, values: dict[str, object]) -> Goal:
        for field, value in values.items():
            setattr(goal, field, value)
        self._session.commit()
        self._session.refresh(goal)
        return goal

    def delete(self, goal: Goal) -> None:
        self._session.delete(goal)
        self._session.commit()