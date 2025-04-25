import asyncio
import logging

from telegram import Bot

from config import BOT_TOKEN, CHAT_ID

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TelegramNotifier:
    """Handles sending messages and images via Telegram bot."""

    def __init__(self):
        if not BOT_TOKEN or not CHAT_ID:
            raise ValueError("BOT_TOKEN or CHAT_ID is not set.")
        self.bot = Bot(token=BOT_TOKEN)
        self.chat_id = CHAT_ID

    def send_message(self, message: str) -> None:
        """Sends a plain text message to Telegram."""
        if type(message) == str:
            asyncio.run(self._async_send(self.bot.send_message, message))
        else:
            logger.info("message is not string")

    def send_image(self, image_path: str, caption: str = "") -> None:
        """Sends an image with optional caption to Telegram."""

        async def send_photo():
            with open(image_path, "rb") as image:
                return await self.bot.send_photo(
                    chat_id=self.chat_id, photo=image, caption=caption
                )

        asyncio.run(self._async_send(send_photo))

    async def _async_send(self, message) -> None:
        async with self.bot:
            try:
                await self.bot.send_message(chat_id=self.chat_id, text=message)
                logger.info("Message sent successfully.")
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
