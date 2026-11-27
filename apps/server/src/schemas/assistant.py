from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class AssistantMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A mensagem não pode estar vazia.")
        return value


class AssistantChatRequest(BaseModel):
    messages: list[AssistantMessage] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_messages(self) -> "AssistantChatRequest":
        if self.messages[-1].role != "user":
            raise ValueError("A última mensagem deve ser do usuário.")
        if sum(len(message.content) for message in self.messages) > 12000:
            raise ValueError("A conversa excede o limite permitido.")
        return self


class AssistantArtifact(BaseModel):
    filename: str = Field(min_length=1, max_length=120)
    content_type: str = Field(min_length=1, max_length=120)
    content_base64: str = Field(min_length=1)


class AssistantBook(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    authors: list[str] = Field(default_factory=list, max_length=5)
    description: str = Field(default="", max_length=700)
    published_date: str | None = Field(default=None, max_length=32)
    info_link: str = Field(min_length=1, max_length=500)


class AssistantChatResponse(BaseModel):
    message: str
    artifacts: list[AssistantArtifact] = Field(default_factory=list)
    books: list[AssistantBook] = Field(default_factory=list, max_length=10)
