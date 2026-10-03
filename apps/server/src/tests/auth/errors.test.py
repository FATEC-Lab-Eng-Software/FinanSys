import pytest

from src.services.auth.errors import AuthFailure, classify_provider_error


class ProviderError(Exception):
    def __init__(self, code=None, status=None):
        super().__init__("provider detail")
        self.code = code
        self.status = status


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (ProviderError(code="invalid_credentials", status=400), 401, "invalid_credentials"),
        (ProviderError(code="over_request_rate_limit", status=429), 429, "login_rate_limited"),
        (ProviderError(code="unexpected_failure", status=500), 503, "authentication_unavailable"),
        (ProviderError(code="unknown_provider_error", status=400), 502, "authentication_failed"),
    ],
)
def test_classify_provider_error_returns_safe_public_failure(error, expected_status, expected_code):
    failure = classify_provider_error(error)

    assert failure.status_code == expected_status
    assert failure.public_code == expected_code
    assert "provider detail" not in failure.public_message


def test_auth_failure_keeps_audit_outcome_separate_from_public_message():
    failure = AuthFailure(401, "invalid_credentials", "E-mail ou senha inválidos.", "invalid_credentials")

    assert failure.audit_outcome == "invalid_credentials"
    assert failure.public_message == "E-mail ou senha inválidos."
