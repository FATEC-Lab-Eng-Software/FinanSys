from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.goal_history import GoalHistory
from src.schemas.goals_schemas import GoalHistoryFilters

class GoalHistoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, *, goal_id: int, value: Decimal) -> GoalHistory:
        entry = GoalHistory(goal_id=goal_id, value=value)
        self._session.add(entry)
        self._session.flush()  
        return entry

    def get(self, *, goal_id: int, history_id: int) -> GoalHistory | None:
        statement = select(GoalHistory).where(
            GoalHistory.id == history_id,
            GoalHistory.goal_id == goal_id,  
        )
        return self._session.scalars(statement).first()

    def list_by_goal(self, *, goal_id: int, filters: GoalHistoryFilters) -> list[GoalHistory]:
        statement = select(GoalHistory).where(GoalHistory.goal_id == goal_id)
        if filters.start is not None:
            statement = statement.where(GoalHistory.created_at >= filters.start)
        if filters.end is not None:
            statement = statement.where(GoalHistory.created_at <= filters.end)
        statement = (
            statement.order_by(GoalHistory.created_at.asc(), GoalHistory.id.asc())
            .limit(filters.limit)
            .offset(filters.offset)
        )
        return list(self._session.scalars(statement))
