import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services import conversation_service


pytestmark = pytest.mark.asyncio


async def test_chat_message_returns_deepseek_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_chat(messages: list[dict[str, str]]) -> str:
        return "Respuesta desde DeepSeek."

    monkeypatch.setattr(
        conversation_service.deepseek_client,
        "chat",
        fake_chat,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/chat/message",
            json={
                "user_id": "dev",
                "conversation_id": None,
                "message": "Hoy leimos un texto y respondimos preguntas.",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["conversation_id"]
    assert payload["reply"] == "Respuesta desde DeepSeek."
    assert payload["state"] == "WAITING_INITIAL_INPUT"
    assert payload["classification"] is None
