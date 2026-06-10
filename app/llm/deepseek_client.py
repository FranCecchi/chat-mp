import asyncio
import sys
from typing import Any

import httpx

from app.core.config import get_settings


class DeepSeekClient:
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 512,
    ) -> str:
        settings = get_settings()

        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Content-Type": "application/json",
        }
        if settings.deepseek_api_key:
            headers["Authorization"] = f"Bearer {settings.deepseek_api_key}"

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                settings.llm_api_url,
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
