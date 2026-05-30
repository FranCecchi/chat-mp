from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import get_settings
from app.services.conversation_service import conversation_service
from app.telegram.client import telegram_bot_client
from app.telegram.handlers import is_start_command, parse_text_message
from app.telegram.messages import START_REPLY


router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, Any]:
    settings = get_settings()
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Telegram webhook secret.",
        )

    update = await request.json()
    inbound_message = parse_text_message(update)
    if inbound_message is None:
        return {"ok": True, "status": "ignored"}

    telegram_user_key = (
        f"{inbound_message.telegram_chat_id}:{inbound_message.telegram_user_id}"
    )
    if is_start_command(inbound_message.text):
        conversation_service.reset_user(telegram_user_key, source="telegram")
        sent = await telegram_bot_client.send_text_message(
            chat_id=inbound_message.telegram_chat_id,
            text=START_REPLY,
        )
        return {
            "ok": True,
            "status": "started",
            "message_sent": sent,
        }

    response = await conversation_service.handle_user_message(
        user_id=telegram_user_key,
        message=inbound_message.text,
        conversation_id=None,
        source="telegram",
    )
    sent = await telegram_bot_client.send_text_message(
        chat_id=inbound_message.telegram_chat_id,
        text=response.reply,
    )

    return {
        "ok": True,
        "status": "processed",
        "message_sent": sent,
        "conversation_id": str(response.conversation_id),
    }
