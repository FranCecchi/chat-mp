from typing import Any

from app.schemas.telegram import TelegramInboundMessage, TelegramMention


def is_start_command(text: str) -> bool:
    command = text.strip().split(maxsplit=1)[0].lower()
    return command == "/start" or command.startswith("/start@")


def parse_text_message(update: dict[str, Any]) -> TelegramInboundMessage | None:
    message = update.get("message")
    if not isinstance(message, dict):
        return None

    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        return None

    user = message.get("from") or {}
    chat = message.get("chat") or {}
    telegram_user_id = user.get("id")
    telegram_chat_id = chat.get("id")

    if not isinstance(telegram_user_id, int) or not isinstance(telegram_chat_id, int):
        return None

    return TelegramInboundMessage(
        telegram_user_id=telegram_user_id,
        telegram_chat_id=telegram_chat_id,
        text=text,
        username=user.get("username"),
        chat_username=chat.get("username"),
        mentions=extract_mentions(text, message.get("entities") or []),
    )


def extract_mentions(text: str, entities: list[dict[str, Any]]) -> list[TelegramMention]:
    mentions: list[TelegramMention] = []

    for entity in entities:
        entity_type = entity.get("type")
        if entity_type == "mention":
            offset = entity.get("offset")
            length = entity.get("length")
            mention_text = None
            if isinstance(offset, int) and isinstance(length, int):
                mention_text = text[offset : offset + length]
            mentions.append(TelegramMention(type="mention", text=mention_text))

        if entity_type == "text_mention":
            mentions.append(
                TelegramMention(
                    type="text_mention",
                    text=None,
                    user=entity.get("user"),
                )
            )

    return mentions
