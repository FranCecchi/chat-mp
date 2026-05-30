from fastapi import APIRouter

from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.conversation_service import conversation_service


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(payload: ChatMessageRequest) -> ChatMessageResponse:
    return await conversation_service.handle_user_message(
        user_id=payload.user_id,
        message=payload.message,
        conversation_id=payload.conversation_id,
        source="api",
    )
