from typing import Any

from pydantic import BaseModel


class TelegramMention(BaseModel):
    type: str
    text: str | None = None
    user: dict[str, Any] | None = None


class TelegramInboundMessage(BaseModel):
    telegram_user_id: int
    telegram_chat_id: int
    text: str
    username: str | None = None
    chat_username: str | None = None
    mentions: list[TelegramMention] = []
