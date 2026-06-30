from fastapi import APIRouter

from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.conversation_service import conversation_service


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(payload: ChatMessageRequest) -> ChatMessageResponse:
    return await conversation_service.handle_user_message(
        user_id=payload.user_id,
        username=payload.username,
        message=payload.message,
        conversation_id=payload.conversation_id,
        source="api",
    )


@router.post("/reset")
async def reset_chat_message(payload: dict) -> dict:
    user_id = payload.get("user_id")
    if user_id:
        conversation_service.reset_user(user_id=user_id, source="api")
        return {"status": "reset", "user_id": user_id}
    return {"status": "error", "message": "user_id is required"}
