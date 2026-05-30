from app.prompts.conversation import (
    PEDAGOGICAL_SYSTEM_PROMPT,
    build_conversation_messages,
)


def test_pedagogical_system_prompt_sets_domain_role() -> None:
    assert "asistente pedagogico" in PEDAGOGICAL_SYSTEM_PROMPT
    assert "movimientos de pensamiento" in PEDAGOGICAL_SYSTEM_PROMPT
    assert "No clasifiques todavia de forma definitiva" in PEDAGOGICAL_SYSTEM_PROMPT
    assert "Si el mensaje no trata sobre una actividad escolar" in PEDAGOGICAL_SYSTEM_PROMPT


def test_build_conversation_messages_adds_system_and_user_messages() -> None:
    messages = build_conversation_messages("Hoy comparamos dos textos.")

    assert messages == [
        {
            "role": "system",
            "content": PEDAGOGICAL_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "Hoy comparamos dos textos.",
        },
    ]


def test_build_conversation_messages_keeps_history_between_system_and_user() -> None:
    history = [
        {"role": "user", "content": "Hoy leimos un texto."},
        {"role": "assistant", "content": "¿Tuvieron que interpretarlo?"},
    ]

    messages = build_conversation_messages(
        "Si, explicamos con nuestras palabras.",
        history=history,
    )

    assert messages == [
        {
            "role": "system",
            "content": PEDAGOGICAL_SYSTEM_PROMPT,
        },
        {"role": "user", "content": "Hoy leimos un texto."},
        {"role": "assistant", "content": "¿Tuvieron que interpretarlo?"},
        {"role": "user", "content": "Si, explicamos con nuestras palabras."},
    ]
