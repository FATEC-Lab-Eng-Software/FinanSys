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


class AssistantChatResponse(BaseModel):
    message: str
