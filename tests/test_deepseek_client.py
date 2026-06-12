import pytest

from app.core.config import get_settings
from app.llm.deepseek_client import DeepSeekClient, parse_reply


def test_parse_reply_returns_first_message_content() -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hola.",
                }
            }
        ]
    }

    assert parse_reply(payload) == "Hola."


def test_parse_reply_rejects_empty_choices() -> None:
    with pytest.raises(ValueError, match="choices"):
        parse_reply({"choices": []})


def test_chat_completions_url_uses_deepseek_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://deepseek.example/v1/")
    get_settings.cache_clear()

    try:
        assert (
            DeepSeekClient().chat_completions_url()
            == "https://deepseek.example/v1/chat/completions"
        )
    finally:
        get_settings.cache_clear()
