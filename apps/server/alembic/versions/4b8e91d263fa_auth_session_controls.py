from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "4b8e91d263fa"
down_revision: Union[str, None] = "9c81f05e2a7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("lockout_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))
    op.execute(
        "UPDATE users SET last_activity_at = last_access_at "
        "WHERE last_activity_at IS NULL AND last_access_at IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("users", "last_activity_at")
    op.drop_column("users", "lockout_until")
