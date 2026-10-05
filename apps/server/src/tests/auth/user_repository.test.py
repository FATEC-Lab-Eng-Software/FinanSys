from datetime import datetime, timezone
from uuid import UUID

import pytest

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

    def execute(self, statement, parameters):
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
