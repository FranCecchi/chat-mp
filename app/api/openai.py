import json
import time
from collections.abc import AsyncIterator
from uuid import uuid4

import anyio
from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.core.config import get_settings
from app.llm.google_genai_client import GoogleGenAIUpstreamError, google_genai_client
from app.schemas.openai import ChatCompletionRequest


router = APIRouter(prefix="/v1", tags=["openai-compatible"])


@router.get("/models")
async def list_models(
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    require_openwebui_auth(authorization)
    model = get_settings().google_genai_model
    return {
        "object": "list",
        "data": [
            {
                "id": model,
                "object": "model",
                "created": 0,
                "owned_by": "chat-mp",
            }
        ],
    }


@router.post("/chat/completions", response_model=None)
async def create_chat_completion(
    payload: ChatCompletionRequest,
    authorization: str | None = Header(default=None),
) -> Response:
    require_openwebui_auth(authorization)
    settings = get_settings()
    if payload.model != settings.google_genai_model:
        return openai_error(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Model '{payload.model}' is not available.",
            error_type="invalid_request_error",
        )

    if payload.tools is not None:
        return openai_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Tool calling is not supported by this backend yet.",
            error_type="invalid_request_error",
        )

    generation_config = build_generation_config(payload)
    completion_id = f"chatcmpl-{uuid4().hex}"
    created = int(time.time())

    if payload.stream:
        return StreamingResponse(
            stream_openai_chunks(
                completion_id=completion_id,
                created=created,
                model=payload.model,
                payload=payload,
                generation_config=generation_config,
            ),
            media_type="text/event-stream",
        )

    try:
        reply = google_genai_client.chat(
            model=payload.model,
            messages=payload.messages,
            generation_config=generation_config,
        )
    except GoogleGenAIUpstreamError as error:
        return openai_error(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=str(error),
            error_type="upstream_error",
        )
    except RuntimeError as error:
        return openai_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(error),
            error_type="configuration_error",
        )
    except ValueError as error:
        return openai_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=str(error),
            error_type="invalid_request_error",
        )

    return JSONResponse(
        {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": payload.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": reply,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": None,
        }
    )


def require_openwebui_auth(authorization: str | None) -> None:
    api_key = get_settings().openwebui_api_key
    if not api_key:
        return

    if authorization != f"Bearer {api_key}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OpenWebUI API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def build_generation_config(payload: ChatCompletionRequest) -> dict[str, object]:
    config: dict[str, object] = {}
    settings = get_settings()
    if payload.temperature is not None:
        config["temperature"] = payload.temperature
    if payload.top_p is not None:
        config["top_p"] = payload.top_p

    max_output_tokens = (
        payload.max_completion_tokens
        or payload.max_tokens
        or settings.google_genai_default_max_output_tokens
    )
    if max_output_tokens is not None:
        config["max_output_tokens"] = max_output_tokens

    if payload.stop is not None:
        config["stop_sequences"] = (
            [payload.stop] if isinstance(payload.stop, str) else payload.stop
        )

    return config


async def stream_openai_chunks(
    *,
    completion_id: str,
    created: int,
    model: str,
    payload: ChatCompletionRequest,
    generation_config: dict[str, object],
) -> AsyncIterator[str]:
    yield encode_sse(
        {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": None,
                }
            ],
        }
    )

    try:
        for text in google_genai_client.stream_chat(
            model=model,
            messages=payload.messages,
            generation_config=generation_config,
        ):
            yield encode_sse(
                {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": text},
                            "finish_reason": None,
                        }
                    ],
                }
            )
            await anyio.sleep(0)
    except GoogleGenAIUpstreamError as error:
        yield encode_sse(
            {
                "error": {
                    "message": str(error),
                    "type": "upstream_error",
                    "param": None,
                    "code": None,
                }
            }
        )
        yield "data: [DONE]\n\n"
        return
    except RuntimeError as error:
        yield encode_sse(
            {
                "error": {
                    "message": str(error),
                    "type": "configuration_error",
                    "param": None,
                    "code": None,
                }
            }
        )
        yield "data: [DONE]\n\n"
        return
    except ValueError as error:
        yield encode_sse(
            {
                "error": {
                    "message": str(error),
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None,
                }
            }
        )
        yield "data: [DONE]\n\n"
        return

    yield encode_sse(
        {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
    )
    yield "data: [DONE]\n\n"


def encode_sse(payload: dict[str, object]) -> str:
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


def openai_error(
    *,
    status_code: int,
    message: str,
    error_type: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": error_type,
                "param": None,
                "code": None,
            }
        },
    )
