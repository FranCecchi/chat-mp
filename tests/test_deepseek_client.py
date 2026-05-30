import pytest

from app.llm.deepseek_client import parse_reply


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
