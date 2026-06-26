from fastapi import APIRouter, Header, HTTPException

from app.core.config import get_settings
from app.services.database import get_all_diagnoses

router = APIRouter(prefix="/teacher", tags=["teacher"])


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
