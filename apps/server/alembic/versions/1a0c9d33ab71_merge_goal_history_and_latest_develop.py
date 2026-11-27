from typing import Union

revision: str = "1a0c9d33ab71"
down_revision: Union[str, tuple[str, str], None] = ("c83430568a97", "f6c2a1d9e0b4")
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
