from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy.dialects.postgresql import dialect

from src.repositories.auth.user_repository import UserRepository


class FakeResult:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class FakeSession:
    def __init__(self, row):
        self.row = row
        self.statement = None
        self.parameters = None
        self.commit_count = 0

    def execute(self, statement, parameters=None):
        self.statement = statement
        self.parameters = parameters
        return FakeResult(self.row)

    def commit(self):
        self.commit_count += 1


@pytest.mark.parametrize(
    ("row", "expected_lockout"),
    [
        ((1, None), None),
        ((5, datetime(2026, 10, 2, 15, 10, tzinfo=timezone.utc)), datetime(2026, 10, 2, 15, 10, tzinfo=timezone.utc)),
    ],
)
def test_failed_attempt_upserts_counter_even_before_user_is_synced(row, expected_lockout):
    session = FakeSession(row)
    repository = UserRepository(session)

    lockout_until = repository.record_failed_login_and_get_lockout(" NewUser@Example.com ")

    statement = str(session.statement)
    assert "INSERT INTO users" in statement
    assert "ON CONFLICT (email) DO UPDATE" in statement
    assert "login_attempts = users.login_attempts + 1" in statement
    assert "users.login_attempts + 1 >= 5" in statement
    assert session.parameters["email"] == "newuser@example.com"
    assert isinstance(session.parameters["id"], UUID)
    assert session.commit_count == 1
    assert lockout_until == expected_lockout


@pytest.mark.parametrize("is_active", [True, False, None])
def test_sync_auth_user_updates_activation_only_when_seed_provides_it(is_active):
    session = FakeSession(None)
    repository = UserRepository(session)

    repository.sync_auth_user(
        user_id=uuid4(),
        email="cliente@finansys.test",
        first_name="Cliente",
        last_name="Demonstração",
        created_at=None,
        last_access_at=None,
        is_active=is_active,
    )

    statement = str(session.statement.compile(dialect=dialect()))
    assert ("is_active = excluded.is_active" in statement) is (is_active is not None)
