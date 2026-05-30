from uuid import UUID

import httpx

from app.llm.deepseek_client import deepseek_client
from app.prompts.conversation import build_conversation_messages
from app.schemas.chat import ChatMessageResponse
from app.services.conversation_memory import ConversationMemory


class ConversationService:
    def __init__(self) -> None:
        self.memory = ConversationMemory()

    async def handle_user_message(
        self,
        user_id: str,
        message: str,
        conversation_id: UUID | None = None,
        source: str = "api",
    ) -> ChatMessageResponse:
        conversation_key = f"{source}:{user_id}"
        active_conversation_id = self.memory.get_conversation_id(
            conversation_key=conversation_key,
            explicit_conversation_id=conversation_id,
        )
        history = self.memory.get_history(active_conversation_id)

        try:
            messages = build_conversation_messages(message, history=history)
            reply = await deepseek_client.chat(messages)
        except RuntimeError:
            reply = "DeepSeek no esta configurado. Revisar DEEPSEEK_API_KEY en .env."
        except (httpx.HTTPError, ValueError):
            reply = "No pude obtener respuesta del modelo en este momento."

        self.memory.append_turn(active_conversation_id, message, reply)

        return ChatMessageResponse(
            conversation_id=active_conversation_id,
            reply=reply,
            state="WAITING_INITIAL_INPUT",
            classification=None,
        )

    def reset_user(self, user_id: str, source: str = "api") -> None:
        self.memory.reset(f"{source}:{user_id}")


conversation_service = ConversationService()
