class AuthFailure(Exception):
    def __init__(
        self,
        status_code: int,
        public_code: str,
        public_message: str,
        audit_outcome: str,
    ) -> None:
        super().__init__(public_message)
        self.status_code = status_code
        self.public_code = public_code
        self.public_message = public_message
        self.audit_outcome = audit_outcome

_CREDENTIAL_CODES = {
    "invalid_credentials",
    "email_not_confirmed",
    "phone_not_confirmed",
    "user_banned",
    "user_not_found",
    "weak_password",
    "refresh_token_not_found",
    "invalid_refresh_token",
    "session_not_found",
    "session_expired",
    "invalid_token",
    "reauthentication_needed",
}
_RATE_LIMIT_CODES = {"over_request_rate_limit", "over_email_send_rate_limit", "over_sms_send_rate_limit"}
_UNAVAILABLE_CODES = {
    "email_provider_disabled",
    "phone_provider_disabled",
    "provider_disabled",
    "no_authorization",
    "unexpected_failure",
    "request_timeout",
    "network_error",
    "server_error",
    "service_unavailable",
    "email_address_not_authorized",
    "validation_failed",
    "captcha_not_enabled",
    "hook_timeout",
    "hook_payload_over_size_limit",
    "manual_linking_disabled",
}

def classify_provider_error(error: Exception) -> AuthFailure:

    code = str(getattr(error, "code", "") or "").lower()
    status = getattr(error, "status", getattr(error, "status_code", None))
    try:
        status = int(status) if status is not None else None
    except (TypeError, ValueError):
        status = None

    if code in _CREDENTIAL_CODES:
        return AuthFailure(401, "invalid_credentials", "E-mail ou senha inválidos.", "invalid_credentials")
    if code in _RATE_LIMIT_CODES or status == 429:
        return AuthFailure(429, "login_rate_limited", "Muitas tentativas. Tente novamente mais tarde.", "rate_limited")
    error_type = type(error).__name__.lower()
    if any(part in error_type for part in ("timeout", "network", "connecterror", "transport")):
        return AuthFailure(503, "authentication_unavailable", "Serviço de autenticação indisponível.", "provider_unavailable")
    if code in _UNAVAILABLE_CODES or status in {403, 500, 501, 503, 504}:
        return AuthFailure(503, "authentication_unavailable", "Serviço de autenticação indisponível.", "provider_unavailable")
    if status is not None and status >= 500:
        return AuthFailure(503, "authentication_unavailable", "Serviço de autenticação indisponível.", "provider_unavailable")

    return AuthFailure(502, "authentication_failed", "Não foi possível concluir a autenticação.", "provider_failure")
