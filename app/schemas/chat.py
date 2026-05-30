from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    conversation_id: UUID | None = None
    message: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    conversation_id: UUID
    reply: str
    state: str
    classification: dict[str, Any] | None = None
