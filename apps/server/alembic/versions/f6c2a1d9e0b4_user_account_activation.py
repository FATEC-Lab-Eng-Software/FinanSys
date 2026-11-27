from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6c2a1d9e0b4"
down_revision: Union[str, None] = "a74d93e1842b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))


def downgrade() -> None:
    op.drop_column("users", "is_active")
