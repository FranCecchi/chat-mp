import logging
from uuid import UUID

from google.api_core.exceptions import (
    ResourceExhausted,
    InvalidArgument,
    ServiceUnavailable,
    PermissionDenied,
    GoogleAPICallError
)

from app.llm.gemini_client import invoke_chain
from app.schemas.chat import ChatMessageResponse
from app.services.conversation_memory import ConversationMemory
from app.services.database import save_diagnosis

logger = logging.getLogger("uvicorn.error")


class ConversationService:
    def __init__(self) -> None:
        self.memory = ConversationMemory()
        # Track student names per conversation for the DB
        self._student_names: dict[UUID, str] = {}
        # Track first user message as activity context
        self._first_messages: dict[UUID, str] = {}

    async def handle_user_message(
        self,
        user_id: str,
        message: str,
        conversation_id: UUID | None = None,
        username: str | None = None,
        source: str = "api",
    ) -> ChatMessageResponse:
        conversation_key = f"{source}:{user_id}"
        active_conversation_id = self.memory.get_conversation_id(
            conversation_key=conversation_key,
            explicit_conversation_id=conversation_id,
        )
        history = self.memory.get_history(active_conversation_id)

        # Store student name on first contact
        if username and active_conversation_id not in self._student_names:
            self._student_names[active_conversation_id] = username

        # Store first message as activity context
        if active_conversation_id not in self._first_messages:
            self._first_messages[active_conversation_id] = message

        classification_data = None
        state = "CHATTING"

        try:
            model_response = await invoke_chain(user_message=message, history=history)
            reply = model_response.reply

            if model_response.is_complete:
                state = "COMPLETED"
                if model_response.movimiento and model_response.movimiento != "Ninguno":
                    classification_data = {
                        "movimiento": model_response.movimiento,
                        "logro": model_response.logro,
                        "justificacion": model_response.justificacion,
                    }
                else:
                    classification_data = {
                        "movimiento": "Ninguno",
                        "logro": "Logro no conseguido",
                        "justificacion": model_response.justificacion or (
                            "La actividad descrita no corresponde a un proceso de aprendizaje escolar "
                            "o no promueve movimientos de pensamiento significativos de la rúbrica."
                        ),
                    }

                # Persist diagnosis to SQLite with full conversation history
                student_name = self._student_names.get(active_conversation_id, username or user_id)
                activity_context = self._first_messages.get(active_conversation_id)
                
                import json
                full_history = list(history)
                full_history.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": reply}
                ])
                conversation_history_json = json.dumps(full_history)

                try:
                    await save_diagnosis(
                        student_name=student_name,
                        conversation_id=str(active_conversation_id),
                        movimiento=classification_data["movimiento"],
                        logro=classification_data["logro"],
                        justificacion=classification_data["justificacion"],
                        activity_context=activity_context,
                        conversation_history=conversation_history_json,
                    )
                except Exception as db_err:
                    logger.error(f"Failed to persist diagnosis: {db_err}", exc_info=True)

        except RuntimeError as e:
            logger.error(f"RuntimeError: {e}")
            reply = "No se configuró la conexión con el asistente. Verificá la clave de acceso del servidor."
            state = "ERROR"
        except ResourceExhausted as e:
            logger.error(f"ResourceExhausted (429): {e}")
            reply = "Se superó el límite de mensajes permitidos. Por favor, esperá unos momentos e intentá de nuevo."
            state = "ERROR"
        except (PermissionDenied, InvalidArgument) as e:
            logger.error(f"Auth error (400/403): {e}")
            reply = "No se pudo autenticar la conexión con el servicio de IA. Verificá la configuración."
            state = "ERROR"
        except (ServiceUnavailable, GoogleAPICallError) as e:
            logger.error(f"API service error: {e}", exc_info=True)
            reply = "El servicio de IA no está disponible en este momento. Por favor, intentá de nuevo más tarde."
            state = "ERROR"
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            reply = "Ocurrió un problema al procesar tu mensaje. Por favor, intentá de nuevo."
            state = "ERROR"

        # Append turn to history
        self.memory.append_turn(active_conversation_id, message, reply)

        return ChatMessageResponse(
            conversation_id=active_conversation_id,
            reply=reply,
            state=state,
            classification=classification_data,
        )

    def reset_user(self, user_id: str, source: str = "api") -> None:
        conversation_key = f"{source}:{user_id}"
        conv_id = self.memory._conversation_ids_by_key.get(conversation_key)
        if conv_id:
            self._student_names.pop(conv_id, None)
            self._first_messages.pop(conv_id, None)
        self.memory.reset(conversation_key)


conversation_service = ConversationService()
