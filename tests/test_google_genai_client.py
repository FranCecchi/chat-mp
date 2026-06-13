import pytest

from app.llm.google_genai_client import build_google_generate_request
from app.prompts.conversation import PEDAGOGICAL_SYSTEM_PROMPT
from app.schemas.openai import OpenAIChatMessage


def test_build_google_request_injects_prompt_and_preserves_history() -> None:
    request = build_google_generate_request(
        messages=[
            OpenAIChatMessage(role="system", content="Responde en una frase."),
            OpenAIChatMessage(
                role="user",
                content="Hoy leimos un texto.",
            ),
            OpenAIChatMessage(
                role="assistant",
                content="Que hicieron con ese texto?",
            ),
            OpenAIChatMessage(
                role="user",
                content="Buscamos evidencias para responder.",
            ),
        ],
        generation_config={
            "temperature": 0.1,
            "top_p": 0.8,
            "max_output_tokens": 100,
            "stop_sequences": ["Final"],
        },
    )

    assert request == {
        "contents": (
            f"{PEDAGOGICAL_SYSTEM_PROMPT}\n\n"
            "Responde en una frase.\n\n"
            "Conversation so far:\n"
            "User: Hoy leimos un texto.\n"
            "Assistant: Que hicieron con ese texto?\n"
            "User: Buscamos evidencias para responder.\n\n"
            "Assistant:"
        ),
        "config": {
            "temperature": 0.1,
            "topP": 0.8,
            "maxOutputTokens": 100,
            "stopSequences": ["Final"],
        },
    }


def test_build_google_request_requires_conversation_content() -> None:
    with pytest.raises(ValueError, match="At least one"):
        build_google_generate_request(
            messages=[OpenAIChatMessage(role="system", content="Solo sistema.")],
            generation_config={},
        )
