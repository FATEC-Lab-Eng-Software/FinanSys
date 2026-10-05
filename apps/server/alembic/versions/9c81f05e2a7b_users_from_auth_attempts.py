from collections.abc import Sequence
from typing import Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9c81f05e2a7b"
down_revision: Union[str, None] = "df3d4badaf3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=20), server_default=sa.text("'client'"), nullable=False),
        sa.Column("login_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_access_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("login_attempts >= 0", name="ck_users_login_attempts_nonnegative"),
        sa.CheckConstraint("role IN ('admin', 'client')", name="ck_users_role_valid"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )


def upgrade() -> None:
    connection = op.get_bind()
    tables = set(sa.inspect(connection).get_table_names(schema="public"))

    if "users" not in tables:
        _create_users_table()

    if "auth_login_attempts" in tables:
        attempts = connection.execute(
            sa.text(
                """
                SELECT lower(email) AS email,
                       count(*) FILTER (WHERE NOT succeeded)::integer AS login_attempts,
                       min(attempted_at) AS created_at,
                       max(attempted_at) FILTER (WHERE succeeded) AS last_access_at
                FROM public.auth_login_attempts
                GROUP BY lower(email)
                """
            )
        ).mappings()

        for attempt in attempts:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO public.users
                        (id, email, role, login_attempts, created_at, last_access_at)
                    VALUES
                        (:id, :email, 'client', :login_attempts, :created_at, :last_access_at)
                    ON CONFLICT (email) DO UPDATE SET
                        login_attempts = public.users.login_attempts + EXCLUDED.login_attempts,
                        created_at = LEAST(public.users.created_at, EXCLUDED.created_at),
                        last_access_at = GREATEST(public.users.last_access_at, EXCLUDED.last_access_at)
                    """
                ),
                {
                    "id": uuid4(),
                    "email": attempt["email"],
                    "login_attempts": attempt["login_attempts"],
                    "created_at": attempt["created_at"],
                    "last_access_at": attempt["last_access_at"],
                },
            )

        op.drop_table("auth_login_attempts")

    if "financial_categories" in tables:
        op.drop_table("financial_categories")


def downgrade() -> None:
    op.drop_table("users")
    op.create_table(
        "auth_login_attempts",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("succeeded", sa.Boolean(), nullable=False),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("remote_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_login_attempts_email", "auth_login_attempts", ["email"])
    op.create_index("ix_auth_login_attempts_attempted_at", "auth_login_attempts", ["attempted_at"])
    op.create_table(
        "financial_categories",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category_type", sa.String(length=20), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("category_type IN ('income', 'expense')", name="ck_financial_categories_type"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_financial_categories_slug"),
    )
