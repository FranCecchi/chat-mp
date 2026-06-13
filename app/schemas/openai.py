from typing import Any, Literal

from pydantic import BaseModel, Field


class OpenAIContentPart(BaseModel):
    type: Literal["text"]
    text: str


class OpenAIChatMessage(BaseModel):
    role: Literal["system", "developer", "user", "assistant"]
    content: str | list[OpenAIContentPart | dict[str, Any]] | None = None


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., min_length=1)
    messages: list[OpenAIChatMessage] = Field(..., min_length=1)
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = Field(default=None, ge=1)
    max_completion_tokens: int | None = Field(default=None, ge=1)
    stop: str | list[str] | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any = None
