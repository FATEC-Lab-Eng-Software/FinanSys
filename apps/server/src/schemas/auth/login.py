from pydantic import BaseModel, Field, field_validator

class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)

    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value: str) -> str:
        value = value.strip()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Endereço de e-mail inválido")
        return value.lower()

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = " ".join(value.strip().split())
        if len(value) < 2:
            raise ValueError("Informe seu nome completo")
        return value

    @field_validator("email")
    @classmethod
    def validate_register_email(cls, value: str) -> str:
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

class PasswordRecoveryRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value: str) -> str:
        value = value.strip()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Endereço de e-mail inválido")
        return value.lower()

class PasswordRecoveryCompleteRequest(BaseModel):
    access_token: str = Field(min_length=1, max_length=4096)
    new_password: str = Field(min_length=8)
