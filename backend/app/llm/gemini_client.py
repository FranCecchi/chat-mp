"""
LangChain-based chat chain using Google Gemini with structured output validation.
"""

import asyncio
import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings
from app.prompts.conversation import BASE_PEDAGOGICAL_SYSTEM_PROMPT
from app.services.rag_service import rag_service

logger = logging.getLogger("uvicorn.error")



class ChatModelResponse(BaseModel):
    reply: str = Field(
        description=(
            "Respuesta conversacional para el estudiante. Si is_complete es False, "
            "esta respuesta debe ser una pregunta breve indagatoria sobre la actividad. "
            "Si is_complete es True, debe ser la explicación pedagógica final de la clasificación."
        )
    )
    is_complete: bool = Field(
        description=(
            "Indica si el análisis ha concluido y se puede clasificar la actividad de forma definitiva (True) "
            "o si se necesita indagar más haciendo preguntas (False)."
        )
    )
    movimiento: Optional[str] = Field(
        None,
        description=(
            "El nombre del movimiento de pensamiento identificado de los 9 oficiales: "
            "'Observar con atención y describir', 'Explicar y dar sentido', 'Justificar con evidencia', "
            "'Relacionar ideas y conceptos', 'Considerar otras perspectivas', 'Identificar ideas claves y llegar a conclusiones', "
            "'Formular preguntas propias', 'Explorar la complejidad del tema', 'Pensar metacognitivamente', "
            "o 'Ninguno' si no corresponde a ninguna actividad pedagógica o movimiento. Debe ser None si is_complete es False."
        )
    )
    logro: Optional[str] = Field(
        None,
        description=(
            "El nivel de logro asignado según la rúbrica oficial: 'Logro esperado', 'Logro parcial' o "
            "'Logro no conseguido'. Debe ser None si is_complete es False o si movimiento es 'Ninguno'."
        )
    )
    justificacion: Optional[str] = Field(
        None,
        description=(
            "Justificación estructurada y concisa citando las respuestas del alumno y la rúbrica oficial. "
            "Debe ser None si is_complete es False o si movimiento es 'Ninguno'."
        )
    )


def _build_lc_messages(
    user_message: str,
    history: list[dict[str, str]],
    system_prompt: str,
) -> list:
    """Convert raw dict history + new user message into LangChain message objects."""
    messages: list = [SystemMessage(content=system_prompt)]

    for turn in history:
        role = turn.get("role")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_message))
    return messages


async def invoke_chain(
    user_message: str,
    history: list[dict[str, str]] | None = None,
) -> ChatModelResponse:
    """
    Build a LangChain Gemini/DeepSeek chain with structured output and invoke it with the history.

    Raises:
        RuntimeError: if API Key is not set.
    """
    settings = get_settings()
    
    # 1. Initialize the LLM based on provider
    if settings.llm_provider == "deepseek":
        if not settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured.")
        
        from langchain_openai import ChatOpenAI
        extra_body = {}
        if settings.deepseek_thinking:
            extra_body["thinking"] = {"type": "enabled"}
            
        llm = ChatOpenAI(
            model=settings.llm_model,
            openai_api_key=settings.deepseek_api_key,
            openai_api_base=settings.deepseek_api_base,
            temperature=0.3,
            extra_body=extra_body,
        )
    else:
        # Default to Gemini
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
            
        llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.3,
        )

    # 2. Get dynamic grounding context and build system prompt
    grounding_context = rag_service.get_grounding_context()
    system_prompt = BASE_PEDAGOGICAL_SYSTEM_PROMPT.format(grounding_context=grounding_context)

    if settings.llm_provider == "deepseek" and settings.deepseek_thinking:
        system_prompt += (
            "\n\nCRITICAL: You MUST respond ONLY with a JSON object matching this schema. "
            "Do not include any extra text, conversational remarks, or markdown wrappers. "
            "The JSON object must match this schema:\n"
            "{\n"
            "  \"reply\": \"Respuesta conversacional para el estudiante.\",\n"
            "  \"is_complete\": true/false,\n"
            "  \"movimiento\": \"Nombre del movimiento o null\",\n"
            "  \"logro\": \"Nivel de logro o null\",\n"
            "  \"justificacion\": \"Justificación o null\"\n"
            "}\n"
        )

    # 3. Create structured chain
    if settings.llm_provider == "deepseek" and settings.deepseek_thinking:
        structured_llm = llm.with_structured_output(ChatModelResponse, method="json_mode")
    else:
        structured_llm = llm.with_structured_output(ChatModelResponse)

    # 4. Format messages and invoke with retries
    messages = _build_lc_messages(user_message, history or [], system_prompt)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await structured_llm.ainvoke(messages)
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Structured LLM failed after {max_retries} attempts: {e}", exc_info=True)
                raise e
            logger.warning(
                f"Structured LLM attempt {attempt + 1} failed: {e}. Retrying in 1 second..."
            )
            await asyncio.sleep(1.0)


async def generate_correction_analysis(
    original_movement: str,
    corrected_movement: str,
    chat_transcript: str
) -> dict[str, str]:
    """
    Generate a corrected pedagogical justification and an explanation of why the original
    classification was incorrect, returning a dict with keys 'justification' and 'error_explanation'.
    """
    settings = get_settings()
    
    # Initialize the LLM based on provider
    if settings.llm_provider == "deepseek":
        if not settings.deepseek_api_key:
            return {
                "justification": f"El docente clasificó esta actividad como '{corrected_movement}'.",
                "error_explanation": f"La clasificación original como '{original_movement}' fue incorrecta."
            }
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=settings.llm_model,
            openai_api_key=settings.deepseek_api_key,
            openai_api_base=settings.deepseek_api_base,
            temperature=0.3,
        )
    else:
        if not settings.gemini_api_key:
            return {
                "justification": f"El docente clasificó esta actividad como '{corrected_movement}'.",
                "error_explanation": f"La clasificación original como '{original_movement}' fue incorrecta."
            }
        llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.3,
        )
        
    if corrected_movement == "Ninguno":
        prompt = (
            f"Sos un asistente pedagógico experto. El docente corrigió el diagnóstico de una actividad de un estudiante.\n"
            f"- El asistente había clasificado originalmente la actividad como: '{original_movement}'\n"
            f"- El docente corrigió la clasificación a: 'Ninguno' (no corresponde a ningún movimiento escolar de la rúbrica).\n\n"
            f"Analizá la siguiente conversación del estudiante:\n"
            f"{chat_transcript}\n\n"
            f"Generá un objeto JSON con dos campos:\n"
            f"1. \"justification\": Una justificación pedagógica breve (de 1 a 3 oraciones) que explique por qué la actividad descrita no corresponde a un proceso de aprendizaje escolar o no promueve movimientos de pensamiento significativos de la rúbrica.\n"
            f"2. \"error_explanation\": Una explicación breve e incisiva (de 1 a 2 oraciones) de por qué clasificar la actividad originalmente como '{original_movement}' fue un error o resultó incorrecto en base a lo que el alumno relata en el chat.\n\n"
            f"Devolvé únicamente el objeto JSON con este formato exacto, sin markdown ni introducciones."
        )
    else:
        prompt = (
            f"Sos un asistente pedagógico experto. El docente corrigió el diagnóstico de una actividad de un estudiante.\n"
            f"- El asistente había clasificado originalmente la actividad como: '{original_movement}'\n"
            f"- El docente corrigió la clasificación al movimiento: '{corrected_movement}' (en su logro esperado).\n\n"
            f"Analizá la siguiente conversación del estudiante:\n"
            f"{chat_transcript}\n\n"
            f"Generá un objeto JSON con dos campos:\n"
            f"1. \"justification\": Una justificación pedagógica breve (de 1 a 3 oraciones) que explique cómo la actividad del alumno demuestra el movimiento '{corrected_movement}', basándote en los criterios de la rúbrica oficial.\n"
            f"2. \"error_explanation\": Una explicación breve e incisiva (de 1 a 2 oraciones) de por qué clasificar la actividad originalmente como '{original_movement}' fue un error o resultó insuficiente en base a lo que el alumno relata en el chat.\n\n"
            f"Devolvé únicamente el objeto JSON con este formato exacto, sin markdown ni introducciones."
        )
    
    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        # Clean potential markdown block wrappers
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                content = "\n".join(lines[1:-1]).strip()
        
        import json
        data = json.loads(content)
        return {
            "justification": data.get("justification", "").strip(),
            "error_explanation": data.get("error_explanation", "").strip()
        }
    except Exception as e:
        logger.error(f"Failed to generate correction analysis: {e}", exc_info=True)
        return {
            "justification": f"El docente clasificó esta actividad como '{corrected_movement}'.",
            "error_explanation": f"La clasificación original como '{original_movement}' fue incorrecta."
        }



