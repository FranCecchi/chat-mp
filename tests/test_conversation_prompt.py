from app.prompts.conversation import (
    PROMPT_QUESTIONER_EXPLORAR,
    PROMPT_SCORER,
    build_llm_messages,
    construir_prompt_questioner,
)


def test_scorer_prompt_sets_domain_and_json_contract() -> None:
    assert "Movimientos de Pensamiento" in PROMPT_SCORER
    assert "Observar con atención y describir" in PROMPT_SCORER
    assert "Pensar metacognitivamente" in PROMPT_SCORER
    assert '"scores"' in PROMPT_SCORER


def test_build_llm_messages_adds_system_before_history() -> None:
    history = [{"role": "user", "content": "Hoy comparamos dos textos."}]
    messages = build_llm_messages(history, PROMPT_SCORER)

    assert messages == [
        {
            "role": "system",
            "content": PROMPT_SCORER,
        },
        {"role": "user", "content": "Hoy comparamos dos textos."},
    ]


def test_build_llm_messages_adds_retrieved_context_to_system_prompt() -> None:
    messages = build_llm_messages(
        [{"role": "user", "content": "Hoy comparamos dos textos."}],
        PROMPT_SCORER,
        "Contexto recuperado de la rubrica.",
    )

    assert "## Contexto RAG" in messages[0]["content"]
    assert "Contexto recuperado de la rubrica." in messages[0]["content"]


def test_construir_prompt_questioner_explores_when_scores_are_low() -> None:
    prompt = construir_prompt_questioner(
        [("Explicar y dar sentido", 0.10)],
        max_score=0.10,
        umbral_explorar=0.15,
    )

    assert prompt == PROMPT_QUESTIONER_EXPLORAR


def test_construir_prompt_questioner_discriminates_between_candidates() -> None:
    prompt = construir_prompt_questioner(
        [
            ("Explicar y dar sentido", 0.70),
            ("Justificar con evidencia", 0.60),
        ],
        max_score=0.70,
        umbral_explorar=0.15,
    )

    assert "Explicar y dar sentido (score: 0.70)" in prompt
    assert "Justificar con evidencia (score: 0.60)" in prompt
    assert "discriminar entre" in prompt
