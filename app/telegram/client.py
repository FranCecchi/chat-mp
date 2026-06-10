from telegram import Bot

from app.core.config import get_settings


class TelegramBotClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.telegram_bot_token)

    async def send_text_message(self, chat_id: int, text: str) -> bool:
        if not self.is_configured:
            return False

        bot = Bot(token=self.settings.telegram_bot_token)
        await bot.send_message(chat_id=chat_id, text=text)
        return True

    async def send_typing_action(self, chat_id: int) -> bool:
        if not self.is_configured:
            return False
        try:
            bot = Bot(token=self.settings.telegram_bot_token)
            await bot.send_chat_action(chat_id=chat_id, action="escribiendo respuesta")
            return True
        except Exception:
            return False

    async def set_webhook(self, public_url: str) -> bool:
        if not self.is_configured:
            return False

        bot = Bot(token=self.settings.telegram_bot_token)
        await bot.set_webhook(
            url=public_url,
            secret_token=self.settings.telegram_webhook_secret,
        )
        return True


telegram_bot_client = TelegramBotClient()
