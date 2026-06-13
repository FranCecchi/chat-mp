import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.api import openai as openai_api
from app.core.config import get_settings
from app.llm.google_genai_client import GoogleGenAIUpstreamError
from app.main import app


pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def reset_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_GENAI_API_KEY", "")
    monkeypatch.setenv("GOOGLE_GENAI_MODEL", "gemini-3.1-flash-lite")
    monkeypatch.setenv("GOOGLE_GENAI_DEFAULT_MAX_OUTPUT_TOKENS", "600")
    monkeypatch.delenv("OPENWEBUI_API_KEY", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_models_returns_configured_gemini_model() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/v1/models")

    assert response.status_code == 200
    assert response.json() == {
        "object": "list",
        "data": [
            {
                "id": "gemini-3.1-flash-lite",
                "object": "model",
                "created": 0,
                "owned_by": "chat-mp",
            }
        ],
    }


async def test_models_rejects_wrong_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENWEBUI_API_KEY", "local-secret")
    get_settings.cache_clear()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/v1/models",
            headers={"Authorization": "Bearer wrong"},
        )

    assert response.status_code == 401


async def test_models_accepts_configured_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENWEBUI_API_KEY", "local-secret")
    get_settings.cache_clear()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/v1/models",
            headers={"Authorization": "Bearer local-secret"},
        )

    assert response.status_code == 200


async def test_chat_completion_returns_openai_compatible_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_chat(
        *,
        model: str,
        messages: list[object],
        generation_config: dict[str, object],
    ) -> str:
        assert model == "gemini-3.1-flash-lite"
        assert messages[-1].role == "user"
        assert generation_config == {
            "temperature": 0.2,
            "max_output_tokens": 100,
        }
        return "Parece una actividad de justificar con evidencia."

    monkeypatch.setattr(openai_api.google_genai_client, "chat", fake_chat)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3.1-flash-lite",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hoy defendimos una respuesta usando citas.",
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 100,
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["object"] == "chat.completion"
    assert payload["model"] == "gemini-3.1-flash-lite"
    assert payload["choices"] == [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Parece una actividad de justificar con evidencia.",
            },
            "finish_reason": "stop",
        }
    ]
    assert payload["usage"] is None


async def test_chat_completion_rejects_unavailable_model() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "other-model",
                "messages": [{"role": "user", "content": "Hola"}],
            },
        )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "invalid_request_error"


async def test_chat_completion_streams_openai_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_stream_chat(
        *,
        model: str,
        messages: list[object],
        generation_config: dict[str, object],
    ) -> list[str]:
        assert model == "gemini-3.1-flash-lite"
        assert generation_config == {"max_output_tokens": 600}
        return ["Primera parte", " y segunda parte."]

    monkeypatch.setattr(
        openai_api.google_genai_client,
        "stream_chat",
        fake_stream_chat,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3.1-flash-lite",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hoy comparamos dos textos.",
                    }
                ],
                "stream": True,
            },
        )

    events = [
        line.removeprefix("data: ")
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    chunks = [json.loads(event) for event in events[:-1]]

    assert response.status_code == 200
    assert events[-1] == "[DONE]"
    assert chunks[0]["choices"][0]["delta"] == {"role": "assistant"}
    assert chunks[1]["choices"][0]["delta"] == {"content": "Primera parte"}
    assert chunks[2]["choices"][0]["delta"] == {"content": " y segunda parte."}
    assert chunks[3]["choices"][0]["finish_reason"] == "stop"


async def test_chat_completion_returns_configuration_error_without_google_key() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3.1-flash-lite",
                "messages": [{"role": "user", "content": "Hola"}],
            },
        )

    assert response.status_code == 500
    assert response.json()["error"]["type"] == "configuration_error"
    assert "GOOGLE_GENAI_API_KEY" in response.json()["error"]["message"]


async def test_chat_completion_returns_upstream_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_chat(
        *,
        model: str,
        messages: list[object],
        generation_config: dict[str, object],
    ) -> str:
        raise GoogleGenAIUpstreamError("Google GenAI error: 500 INTERNAL")

    monkeypatch.setattr(openai_api.google_genai_client, "chat", fail_chat)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3.1-flash-lite",
                "messages": [{"role": "user", "content": "Hola"}],
            },
        )

    assert response.status_code == 502
    assert response.json()["error"]["type"] == "upstream_error"
    assert "500 INTERNAL" in response.json()["error"]["message"]


async def test_chat_completion_rejects_tools() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3.1-flash-lite",
                "messages": [{"role": "user", "content": "Hola"}],
                "tools": [{"type": "function"}],
            },
        )

    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_request_error"


async def test_chat_completion_allows_mixed_content_parts_when_text_is_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_chat(
        *,
        model: str,
        messages: list[object],
        generation_config: dict[str, object],
    ) -> str:
        assert model == "gemini-3.1-flash-lite"
        assert generation_config == {"max_output_tokens": 600}
        assert messages[-1].content[0].text == "Describe lo relevante si aplica."
        assert messages[-1].content[1]["type"] == "image_url"
        return "Puedo responder con el texto disponible."

    monkeypatch.setattr(openai_api.google_genai_client, "chat", fake_chat)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3.1-flash-lite",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe lo relevante si aplica.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": "data:image/png;base64,abc"},
                            },
                        ],
                    }
                ],
            },
        )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == (
        "Puedo responder con el texto disponible."
    )
