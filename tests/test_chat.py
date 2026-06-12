import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services import conversation_service


pytestmark = pytest.mark.asyncio


async def test_chat_message_returns_deepseek_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replies = iter(
        [
            """
            {
              "scores": {
                "Observar con atención y describir": 0.1,
                "Explicar y dar sentido": 0.6,
                "Justificar con evidencia": 0.2
              },
              "razonamiento": "La respuesta sugiere explicación, pero falta detalle."
            }
            """,
            """
            {
              "pregunta": "¿Qué tuvieron que explicar con sus propias palabras?",
              "razonamiento": "Necesito discriminar entre explicación y evidencia."
            }
            """,
        ]
    )

    async def fake_chat(messages: list[dict[str, str]]) -> str:
        return next(replies)

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
    assert payload["reply"] == "¿Qué tuvieron que explicar con sus propias palabras?"
    assert payload["state"] == "WAITING_INITIAL_INPUT"
    assert payload["classification"] is None
