"""create goal_history

Revision ID: c83430568a97
Revises: df023ce708c3
Create Date: 2026-11-26 22:30:43.230060
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c83430568a97'
down_revision: Union[str, None] = 'df023ce708c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "goal_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("value <> 0", name="ck_goal_history_value_nonzero"),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_goal_history_goal_id_created_at",
        "goal_history",
        ["goal_id", "created_at"],
    )
    op.execute(
        """
        INSERT INTO goal_history (goal_id, value, created_at)
        SELECT id, accumulated_value, created_at
        FROM goals
        WHERE accumulated_value > 0
        """
    )


def downgrade() -> None:
    op.drop_index("ix_goal_history_goal_id_created_at", table_name="goal_history")
    op.drop_table("goal_history")
