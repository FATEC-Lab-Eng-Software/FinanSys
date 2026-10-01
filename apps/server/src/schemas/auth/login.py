from pydantic import BaseModel, Field, field_validator

class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)

    password: str = Field(min_length=1, max_length=1024)

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value: str) -> str:
        value = value.strip()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Endereço de e-mail inválido")
        return value.lower()

class AuthenticatedUser(BaseModel):
    id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None

class LoginResponse(BaseModel):
    user: AuthenticatedUser
    expires_in: int
