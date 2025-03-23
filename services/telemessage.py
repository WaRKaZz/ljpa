import logging
import asyncio
from telegram import Bot
from consts import BOT_TOKEN, CHAT_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        if not BOT_TOKEN or not CHAT_ID:
            raise ValueError("BOT_TOKEN or CHAT_ID is not set.")
        self.bot = Bot(token=BOT_TOKEN)
        self.chat_id = CHAT_ID

    async def async_send_message(self, message: str):
        async with self.bot:
            try:
                await self.bot.send_message(chat_id=self.chat_id, text=message)
                logger.info("Message sent successfully.")
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

    def send_message(self, message: str):
        asyncio.run(self.async_send_message(message))

    async def async_send_image(self, image_path: str, caption: str = ""):
        async with self.bot:
            try:
                with open(image_path, "rb") as image:
                    await self.bot.send_photo(chat_id=self.chat_id, photo=image, caption=caption)
                logger.info("Image sent successfully.")
            except Exception as e:
                logger.error(f"Failed to send image: {e}")

    def send_image(self, image_path: str, caption: str = ""):
        asyncio.run(self.async_send_image(image_path, caption))
