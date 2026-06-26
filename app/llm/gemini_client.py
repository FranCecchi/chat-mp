import asyncio
import sys
from typing import Any

import httpx

from app.core.config import get_settings


class GeminiClient:
    async def chat(self, messages: list[dict[str, str]]) -> str:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        # Extract system prompt if present
        system_instruction = None
        contents = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {
                    "parts": [{"text": content}]
                }
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })

        payload = {
            "contents": contents,
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        headers = {
            "Content-Type": "application/json",
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        return parse_reply(data)


def parse_reply(data: dict[str, Any]) -> str:
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Gemini response does not include candidates.")

    content = candidates[0].get("content")
    if not isinstance(content, dict):
        raise ValueError("Gemini response does not include content.")

    parts = content.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ValueError("Gemini response content does not include parts.")

    text = parts[0].get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Gemini response text is empty.")

    return text.strip()


gemini_client = GeminiClient()


async def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m app.llm.gemini_client <message>")
        return 2

    message = " ".join(sys.argv[1:])
    try:
        reply = await gemini_client.chat([{"role": "user", "content": message}])
        print(reply)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
