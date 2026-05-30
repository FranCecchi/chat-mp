import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app
from app.services import conversation_service
from app.telegram import router as telegram_router
from app.telegram.messages import START_REPLY


pytestmark = pytest.mark.asyncio


async def test_telegram_webhook_rejects_invalid_secret() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
            json={},
        )

    assert response.status_code == 403


async def test_telegram_webhook_ignores_unsupported_update() -> None:
    settings = get_settings()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/telegram/webhook",
            headers={
                "X-Telegram-Bot-Api-Secret-Token": settings.telegram_webhook_secret
            },
            json={"update_id": 1},
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True, "status": "ignored"}


async def test_telegram_webhook_processes_text_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_chat(messages: list[dict[str, str]]) -> str:
        return "Respuesta desde DeepSeek."

    async def fake_send_text_message(chat_id: int, text: str) -> bool:
        assert chat_id == 456
        assert text == "Respuesta desde DeepSeek."
        return False

    monkeypatch.setattr(
        conversation_service.deepseek_client,
        "chat",
        fake_chat,
    )
    monkeypatch.setattr(
        telegram_router.telegram_bot_client,
        "send_text_message",
        fake_send_text_message,
    )

    settings = get_settings()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/telegram/webhook",
            headers={
                "X-Telegram-Bot-Api-Secret-Token": settings.telegram_webhook_secret
            },
            json={
                "update_id": 1,
                "message": {
                    "message_id": 10,
                    "from": {"id": 123, "is_bot": False, "username": "ana"},
                    "chat": {"id": 456, "type": "private", "username": "ana"},
                    "text": "Hoy comparamos dos textos.",
                },
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["status"] == "processed"
    assert payload["message_sent"] is False
    assert payload["conversation_id"]


async def test_telegram_webhook_start_resets_memory_and_sends_welcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_messages: list[tuple[int, str]] = []

    async def fail_chat(messages: list[dict[str, str]]) -> str:
        raise AssertionError("/start should not call the LLM")

    async def fake_send_text_message(chat_id: int, text: str) -> bool:
        sent_messages.append((chat_id, text))
        return True

    monkeypatch.setattr(
        conversation_service.deepseek_client,
        "chat",
        fail_chat,
    )
    monkeypatch.setattr(
        telegram_router.telegram_bot_client,
        "send_text_message",
        fake_send_text_message,
    )

    settings = get_settings()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/telegram/webhook",
            headers={
                "X-Telegram-Bot-Api-Secret-Token": settings.telegram_webhook_secret
            },
            json={
                "update_id": 1,
                "message": {
                    "message_id": 10,
                    "from": {"id": 123, "is_bot": False, "username": "ana"},
                    "chat": {"id": 456, "type": "private", "username": "ana"},
                    "text": "/start",
                    "entities": [{"type": "bot_command", "offset": 0, "length": 6}],
                },
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "status": "started",
        "message_sent": True,
    }
    assert sent_messages == [(456, START_REPLY)]
