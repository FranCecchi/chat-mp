import asyncio
import sys
from typing import Any

import httpx

from app.core.config import get_settings


class DeepSeekClient:
    async def chat(self, messages: list[dict[str, str]]) -> str:
        settings = get_settings()
        if not settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured.")

        payload = {
            "model": settings.deepseek_model,
            "messages": messages,
        }
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        return parse_reply(data)


def parse_reply(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("DeepSeek response does not include choices.")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("DeepSeek response does not include a message.")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("DeepSeek response message is empty.")

    return content.strip()


deepseek_client = DeepSeekClient()


async def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m app.llm.deepseek_client <message>")
        return 2

    message = " ".join(sys.argv[1:])
    reply = await deepseek_client.chat([{"role": "user", "content": message}])
    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
