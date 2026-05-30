from uuid import UUID, uuid4


class ConversationMemory:
    def __init__(self, max_messages: int = 8) -> None:
        self.max_messages = max_messages
        self._conversation_ids_by_key: dict[str, UUID] = {}
        self._messages_by_conversation_id: dict[UUID, list[dict[str, str]]] = {}

    def get_conversation_id(
        self,
        conversation_key: str,
        explicit_conversation_id: UUID | None = None,
    ) -> UUID:
        if explicit_conversation_id is not None:
            self._messages_by_conversation_id.setdefault(explicit_conversation_id, [])
            return explicit_conversation_id

        if conversation_key not in self._conversation_ids_by_key:
            self._conversation_ids_by_key[conversation_key] = uuid4()

        conversation_id = self._conversation_ids_by_key[conversation_key]
        self._messages_by_conversation_id.setdefault(conversation_id, [])
        return conversation_id

    def get_history(self, conversation_id: UUID) -> list[dict[str, str]]:
        return list(self._messages_by_conversation_id.get(conversation_id, []))

    def append_turn(self, conversation_id: UUID, user_message: str, assistant_reply: str) -> None:
        history = self._messages_by_conversation_id.setdefault(conversation_id, [])
        history.extend(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_reply},
            ]
        )
        self._messages_by_conversation_id[conversation_id] = history[
            -self.max_messages :
        ]

    def reset(self, conversation_key: str) -> None:
        conversation_id = self._conversation_ids_by_key.pop(conversation_key, None)
        if conversation_id is not None:
            self._messages_by_conversation_id.pop(conversation_id, None)
