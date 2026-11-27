from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class GoalHistory(Base):
    __tablename__ = "goal_history"
    __table_args__ = (
        CheckConstraint("value <> 0", name="ck_goal_history_value_nonzero"),
        Index("ix_goal_history_goal_id_created_at", "goal_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )