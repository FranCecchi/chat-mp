from app.services.conversation_memory import ConversationMemory


def test_memory_reuses_conversation_id_for_same_key() -> None:
    memory = ConversationMemory()

    first_id = memory.get_conversation_id("telegram:1:2")
    second_id = memory.get_conversation_id("telegram:1:2")

    assert second_id == first_id


def test_memory_stores_and_limits_recent_messages() -> None:
    memory = ConversationMemory(max_messages=2)
    conversation_id = memory.get_conversation_id("telegram:1:2")

    memory.append_turn(conversation_id, "mensaje 1", "respuesta 1")
    memory.append_turn(conversation_id, "mensaje 2", "respuesta 2")

    assert memory.get_history(conversation_id) == [
        {"role": "user", "content": "mensaje 2"},
        {"role": "assistant", "content": "respuesta 2"},
    ]


def test_memory_reset_forgets_existing_conversation() -> None:
    memory = ConversationMemory()
    first_id = memory.get_conversation_id("telegram:1:2")
    memory.append_turn(first_id, "hola", "respuesta")

    memory.reset("telegram:1:2")
    second_id = memory.get_conversation_id("telegram:1:2")

    assert second_id != first_id
    assert memory.get_history(first_id) == []
