import pytest

from app.services import conversation_service as conversation_module
from app.services.conversation_service import ConversationService


pytestmark = pytest.mark.asyncio


async def test_conversation_injects_rag_context_into_scorer_and_questioner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[dict[str, str]]] = []
    replies = iter(
        [
            """
            {
              "scores": {
                "Explicar y dar sentido": 0.6,
                "Justificar con evidencia": 0.2
              }
            }
            """,
            """
            {
              "pregunta": "¿Qué tuvieron que explicar?",
              "razonamiento": "Pregunta de seguimiento."
            }
            """,
        ]
    )

    def fake_build_context(
        *,
        message: str,
        history: list[dict[str, str]],
    ) -> str:
        assert message == "Hoy explicamos un texto."
        assert history == []
        return "Contexto recuperado de prueba."

    async def fake_chat(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return next(replies)

    monkeypatch.setattr(
        conversation_module.rag_service,
        "build_context",
        fake_build_context,
    )
    monkeypatch.setattr(conversation_module.deepseek_client, "chat", fake_chat)

    service = ConversationService()
    response = await service.handle_user_message(
        user_id="dev",
        message="Hoy explicamos un texto.",
    )

    assert response.reply == "¿Qué tuvieron que explicar?"
    assert len(calls) == 2
    assert all("Contexto recuperado de prueba." in call[0]["content"] for call in calls)


async def test_conversation_injects_rag_context_into_classifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[dict[str, str]]] = []
    replies = iter(
        [
            """
            {
              "scores": {
                "Justificar con evidencia": 0.9,
                "Explicar y dar sentido": 0.3
              }
            }
            """,
            """
            {
              "mensaje_alumno": "Trabajaste justificando con evidencia.",
              "razonamiento": "El score fue alto."
            }
            """,
        ]
    )

    def fake_build_context(
        *,
        message: str,
        history: list[dict[str, str]],
    ) -> str:
        return "Contexto de rubrica para clasificar."

    async def fake_chat(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return next(replies)

    monkeypatch.setattr(
        conversation_module.rag_service,
        "build_context",
        fake_build_context,
    )
    monkeypatch.setattr(conversation_module.deepseek_client, "chat", fake_chat)

    service = ConversationService()
    response = await service.handle_user_message(
        user_id="dev",
        message="Justificamos con datos del texto.",
    )

    assert response.state == "COMPLETED"
    assert response.reply == "Trabajaste justificando con evidencia."
    assert len(calls) == 2
    assert all("Contexto de rubrica para clasificar." in call[0]["content"] for call in calls)
