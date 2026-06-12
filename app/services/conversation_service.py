import json
from uuid import UUID

import httpx

from app.llm.deepseek_client import deepseek_client
from app.prompts.conversation import (
    PROMPT_CLASIFICAR,
    PROMPT_SCORER,
    build_llm_messages,
    construir_prompt_questioner,
)
from app.rag.service import rag_service
from app.schemas.chat import ChatMessageResponse
from app.services.conversation_memory import ConversationMemory

# Constantes de configuración de la lógica de Lucía
MAX_TURNOS = 3
UMBRAL_CLASIFICAR = 0.85  # score mínimo del top-1 para clasificar como "logro esperado"
UMBRAL_EXPLORAR = 0.15  # si el top-1 está por debajo de esto -> pregunta general


def parsear_json(texto: str) -> dict | None:
    """Extrae y parsea el JSON de la respuesta del modelo."""
    try:
        # El modelo a veces envuelve el JSON en ```json ... ```
        if "```" in texto:
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        return json.loads(texto.strip())
    except (json.JSONDecodeError, IndexError):
        return None


def obtener_top_3(scores: dict) -> list[tuple[str, float]]:
    """Devuelve los 3 movimientos con mayor score, ordenados de mayor a menor."""
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]


def score_a_nivel_logro(score: float) -> str:
    """Convierte un score numérico al nivel de logro de la rúbrica."""
    if score >= UMBRAL_CLASIFICAR:
        return "esperado"
    elif score >= 0.50:
        return "parcial"
    else:
        return "no conseguido"


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

        # Calculamos los turnos basándonos en la cantidad de mensajes de usuario previos
        turnos = sum(1 for m in history if m["role"] == "user")

        # Creamos un historial temporal que incluya el mensaje actual del alumno
        temp_history = history + [{"role": "user", "content": message}]
        retrieved_context = rag_service.build_context(
            message=message,
            history=history,
        )

        try:
            # ── LLAMADA 1: SCORER ──
            messages_scorer = build_llm_messages(
                temp_history,
                PROMPT_SCORER,
                retrieved_context,
            )
            respuesta_scorer = await deepseek_client.chat(messages_scorer)
            datos_scorer = parsear_json(respuesta_scorer)

            if datos_scorer is None or "scores" not in datos_scorer:
                # Fallback si falla el parseo
                reply = "No pude analizar tu respuesta correctamente. ¿Me contarías un poco más?"
                self.memory.append_turn(active_conversation_id, message, reply)
                return ChatMessageResponse(
                    conversation_id=active_conversation_id,
                    reply=reply,
                    state="WAITING_INITIAL_INPUT",
                    classification=None,
                )

            scores = datos_scorer["scores"]
            top_3 = obtener_top_3(scores)
            max_mov, max_score = top_3[0]

            # Decidimos si debemos clasificar y cerrar la conversación
            # turnos + 1 representa la interacción actual del usuario
            debe_clasificar = (max_score >= UMBRAL_CLASIFICAR) or (
                (turnos + 1) >= MAX_TURNOS
            )

            if debe_clasificar:
                nivel_logro = score_a_nivel_logro(max_score)
                movimiento = max_mov if max_score >= UMBRAL_EXPLORAR else "ninguno"

                # ── LLAMADA 2: CLASIFICAR ──
                prompt_cls = PROMPT_CLASIFICAR.format(
                    movimiento=movimiento,
                    nivel_logro=nivel_logro,
                )
                messages_cls = build_llm_messages(
                    temp_history,
                    prompt_cls,
                    retrieved_context,
                )
                respuesta_cls = await deepseek_client.chat(messages_cls)
                datos_cls = parsear_json(respuesta_cls)

                if datos_cls is None or "mensaje_alumno" not in datos_cls:
                    reply = (
                        f"¡Gracias por contarme! Evalué tu actividad y el principal "
                        f"movimiento identificado es '{movimiento}' con un nivel de logro '{nivel_logro}'."
                    )
                    razonamiento_final = "Fallback de clasificación debido a error de parseo JSON."
                else:
                    reply = datos_cls["mensaje_alumno"]
                    razonamiento_final = datos_cls.get("razonamiento", "")

                classification_data = {
                    "movimiento": movimiento,
                    "nivel_logro": nivel_logro,
                    "max_score": float(max_score),
                    "scores": scores,
                    "razonamiento": razonamiento_final,
                }

                # Como la conversación finalizó, reiniciamos la memoria para este usuario
                # de modo que la próxima interacción comience una nueva sesión de chat.
                self.memory.reset(conversation_key)

                return ChatMessageResponse(
                    conversation_id=active_conversation_id,
                    reply=reply,
                    state="COMPLETED",
                    classification=classification_data,
                )

            else:
                # ── LLAMADA 2: QUESTIONER ──
                prompt_q = construir_prompt_questioner(
                    top_3, max_score, UMBRAL_EXPLORAR
                )
                messages_q = build_llm_messages(
                    temp_history,
                    prompt_q,
                    retrieved_context,
                )
                respuesta_q = await deepseek_client.chat(messages_q)
                datos_q = parsear_json(respuesta_q)

                if datos_q is None or "pregunta" not in datos_q:
                    reply = "¿Podrías darme más detalles sobre lo que hicieron en la clase?"
                else:
                    reply = datos_q["pregunta"]

                # Guardamos la conversación (mensaje del usuario + pregunta generada)
                self.memory.append_turn(active_conversation_id, message, reply)

                return ChatMessageResponse(
                    conversation_id=active_conversation_id,
                    reply=reply,
                    state="WAITING_INITIAL_INPUT",
                    classification=None,
                )

        except (httpx.HTTPError, ValueError):
            reply = "No pude obtener respuesta del modelo en este momento. Intentá nuevamente."
            return ChatMessageResponse(
                conversation_id=active_conversation_id,
                reply=reply,
                state="WAITING_INITIAL_INPUT",
                classification=None,
            )

    def reset_user(self, user_id: str, source: str = "api") -> None:
        self.memory.reset(f"{source}:{user_id}")


conversation_service = ConversationService()
