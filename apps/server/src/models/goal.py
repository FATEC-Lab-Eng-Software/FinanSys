from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base

class GoalStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"

class GoalCategory(StrEnum):
    WORK = "work"
    HOUSING = "housing"
    UTILITIES = "utilities"
    FOOD = "food"
    TRANSPORTATION = "transportation"
    MEDICAL = "medical"
    PETS = "pets"
    TRAVEL = "travel"
    OTHER = "other"

class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'done')", name="ck_goals_status_valid"),
        CheckConstraint("target_value > 0", name="ck_goals_target_value_positive"),
        CheckConstraint("accumulated_value >= 0", name="ck_goals_accumulated_value_nonnegative"),
        Index("ix_goals_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    accumulated_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0"), server_default=text("0")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=GoalStatus.PENDING.value, server_default=text("'pending'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )