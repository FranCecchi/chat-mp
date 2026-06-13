from collections.abc import Iterator
from typing import Any

import httpx

from app.core.config import get_settings
from app.prompts.conversation import PEDAGOGICAL_SYSTEM_PROMPT
from app.schemas.openai import OpenAIChatMessage


class GoogleGenAIUpstreamError(RuntimeError):
    pass


class GoogleGenAIClient:
    def chat(
        self,
        *,
        model: str,
        messages: list[OpenAIChatMessage],
        generation_config: dict[str, Any],
    ) -> str:
        client = self._create_client()
        request = build_google_generate_request(
            messages=messages,
            generation_config=generation_config,
        )
        try:
            response = client.models.generate_content(model=model, **request)
        except Exception as error:
            raise_google_api_error(error)

        text = getattr(response, "text", "")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Google GenAI response text is empty.")
        return text.strip()

    def stream_chat(
        self,
        *,
        model: str,
        messages: list[OpenAIChatMessage],
        generation_config: dict[str, Any],
    ) -> Iterator[str]:
        client = self._create_client()
        request = build_google_generate_request(
            messages=messages,
            generation_config=generation_config,
        )
        try:
            stream = client.models.generate_content_stream(model=model, **request)
        except Exception as error:
            raise_google_api_error(error)

        for chunk in stream:
            try:
                text = getattr(chunk, "text", "")
                if isinstance(text, str) and text:
                    yield text
            except Exception as error:
                raise_google_api_error(error)

    def _create_client(self) -> Any:
        settings = get_settings()
        if not settings.google_genai_api_key:
            raise RuntimeError("GOOGLE_GENAI_API_KEY is not configured.")

        from google import genai

        return genai.Client(api_key=settings.google_genai_api_key)


def build_google_generate_request(
    *,
    messages: list[OpenAIChatMessage],
    generation_config: dict[str, Any],
) -> dict[str, Any]:
    system_messages: list[str] = [PEDAGOGICAL_SYSTEM_PROMPT]
    conversation_lines: list[str] = []

    for message in messages:
        text = extract_text_content(message)
        if message.role in {"system", "developer"}:
            if text:
                system_messages.append(text)
            continue

        if not text:
            continue

        label = "Assistant" if message.role == "assistant" else "User"
        conversation_lines.append(f"{label}: {text}")

    if not conversation_lines:
        raise ValueError("At least one user or assistant message is required.")

    request: dict[str, Any] = {
        "contents": (
            f"{'\n\n'.join(system_messages)}\n\n"
            "Conversation so far:\n"
            f"{'\n'.join(conversation_lines)}\n\n"
            "Assistant:"
        )
    }

    google_config = build_google_generation_config(generation_config)
    if google_config:
        request["config"] = google_config

    return request


def build_google_generation_config(generation_config: dict[str, Any]) -> dict[str, Any]:
    key_map = {
        "temperature": "temperature",
        "top_p": "topP",
        "max_output_tokens": "maxOutputTokens",
        "stop_sequences": "stopSequences",
    }
    return {
        google_key: generation_config[source_key]
        for source_key, google_key in key_map.items()
        if source_key in generation_config
    }


def extract_text_content(message: OpenAIChatMessage) -> str:
    if message.content is None:
        return ""

    if isinstance(message.content, str):
        return message.content.strip()

    text_parts: list[str] = []
    for part in message.content:
        if isinstance(part, OpenAIContentPart):
            text_parts.append(part.text)
        elif isinstance(part, dict) and part.get("type") == "text":
            text = part.get("text")
            if isinstance(text, str):
                text_parts.append(text)

    return "\n".join(text_parts).strip()


def raise_google_api_error(error: Exception) -> None:
    from google.genai import errors

    if isinstance(error, errors.APIError):
        raise GoogleGenAIUpstreamError(f"Google GenAI error: {error}") from error

    if isinstance(error, httpx.HTTPError):
        raise GoogleGenAIUpstreamError(f"Google GenAI network error: {error}") from error

    raise error


google_genai_client = GoogleGenAIClient()
