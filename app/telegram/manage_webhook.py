import asyncio
import json
import sys

from telegram import Bot

from app.core.config import get_settings


def usage() -> None:
    print("Usage:")
    print("  python -m app.telegram.manage_webhook set <public-webhook-url>")
    print("  python -m app.telegram.manage_webhook info")
    print("  python -m app.telegram.manage_webhook delete")


def get_bot() -> Bot | None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN is not configured.")
        return None
    return Bot(token=settings.telegram_bot_token)


async def set_webhook(public_url: str) -> int:
    settings = get_settings()
    bot = get_bot()
    if bot is None:
        return 1

    await bot.set_webhook(
        url=public_url,
        secret_token=settings.telegram_webhook_secret,
    )
    print(f"Telegram webhook registered: {public_url}")
    return 0


async def get_webhook_info() -> int:
    bot = get_bot()
    if bot is None:
        return 1

    info = await bot.get_webhook_info()
    print(json.dumps(info.to_dict(), indent=2, ensure_ascii=False))
    return 0


async def delete_webhook() -> int:
    bot = get_bot()
    if bot is None:
        return 1

    await bot.delete_webhook(drop_pending_updates=False)
    print("Telegram webhook deleted.")
    return 0


async def main() -> int:
    if len(sys.argv) < 2:
        usage()
        return 2

    command = sys.argv[1]
    if command == "set" and len(sys.argv) == 3:
        return await set_webhook(sys.argv[2])
    if command == "info" and len(sys.argv) == 2:
        return await get_webhook_info()
    if command == "delete" and len(sys.argv) == 2:
        return await delete_webhook()

    usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
