from fastapi import APIRouter, Header, HTTPException

from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.services.database import get_all_diagnoses, get_diagnosis, submit_diagnosis_feedback
from app.services.rag_service import rag_service

router = APIRouter(prefix="/teacher", tags=["teacher"])


class FeedbackRequest(BaseModel):
    diagnosis_id: int
    is_correct: bool
    correct_movement: str | None = None


def _check_password(x_teacher_password: str) -> None:
    settings = get_settings()
    if not settings.teacher_password:
        raise HTTPException(status_code=503, detail="Teacher access not configured.")
    if x_teacher_password != settings.teacher_password:
        raise HTTPException(status_code=401, detail="Invalid teacher password.")


@router.get("/history")
async def get_history(x_teacher_password: str = Header(...)) -> list[dict]:
    """Return all completed diagnoses ordered by date descending."""
    _check_password(x_teacher_password)
    return await get_all_diagnoses()


@router.post("/feedback")
async def submit_feedback(
    payload: FeedbackRequest,
    x_teacher_password: str = Header(...)
) -> dict:
    """Submit teacher feedback (correct/incorrect classification) for a diagnosis."""
    _check_password(x_teacher_password)
    
    # 1. Fetch diagnosis from database
    diagnosis = await get_diagnosis(payload.diagnosis_id)
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found.")
        
    # 2. Determine feedback status and details to append
    status = "correct" if payload.is_correct else "incorrect"
    corrected_movement = payload.correct_movement if not payload.is_correct else None
    
    # 3. Update database
    await submit_diagnosis_feedback(
        diagnosis_id=payload.diagnosis_id,
        status=status,
        corrected_movement=corrected_movement
    )
    
    # 4. Extract and parse conversation history
    history_str = diagnosis.get("conversation_history")
    conversation = []
    chat_transcript = ""
    
    if history_str:
        try:
            import json
            conversation = json.loads(history_str)
            formatted_turns = []
            for turn in conversation:
                role = "Alumno" if turn.get("role") == "user" else "Asistente"
                content = turn.get("content", "").strip()
                if content:
                    formatted_turns.append(f"{role}: {content}")
            if formatted_turns:
                chat_transcript = "\n".join(formatted_turns)
        except Exception as e:
            import logging
            logging.getLogger("uvicorn.error").error(
                f"Failed to parse conversation history: {e}", exc_info=True
            )

    original_mov = diagnosis.get("movimiento")
    original_logro = diagnosis.get("logro")
    error_explanation = None
    
    # 5. Determine corrected movement and logro
    if payload.is_correct:
        corrected_mov = original_mov
        corrected_logro = original_logro
        justification = diagnosis.get("justificacion") or ""
    else:
        corrected_mov = payload.correct_movement
        corrected_logro = "Logro esperado"  # Defaults to logro esperado when corrected
        
        justification = f"El docente clasificó esta actividad como '{payload.correct_movement}'."
        error_explanation = f"La clasificación original como '{original_mov}' fue insuficiente."
        if chat_transcript:
            try:
                from app.llm.gemini_client import generate_correction_analysis
                analysis = await generate_correction_analysis(
                    original_movement=original_mov,
                    corrected_movement=payload.correct_movement,
                    chat_transcript=chat_transcript
                )
                justification = analysis.get("justification") or justification
                error_explanation = analysis.get("error_explanation") or error_explanation
            except Exception as e:
                import logging
                logging.getLogger("uvicorn.error").error(
                    f"Failed to generate correction analysis: {e}", exc_info=True
                )

    # 6. Append to JSON and reload RAG
    rag_service.append_feedback_to_json(
        activity_context=diagnosis.get("activity_context") or "",
        is_correct=payload.is_correct,
        original_movement=original_mov,
        original_logro=original_logro,
        corrected_movement=corrected_mov,
        corrected_logro=corrected_logro,
        justification=justification,
        error_explanation=error_explanation,
        conversation=conversation
    )
    
    return {"status": "success", "feedback_status": status}



