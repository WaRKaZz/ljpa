import logging
import os
from datetime import datetime

from database.repository import TextEntryRepository
from services.gpt_processor import GPTProcessor
from services.linkedin import startLinkedinScrapper
from utilities.file_handler import save_screenshot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInProcessor:
    def __init__(self):
        self.repo = TextEntryRepository()
        self._gpt_processor = GPTProcessor()

    def process_posts(self):
        """Main workflow for processing LinkedIn posts"""
        posts = startLinkedinScrapper()
        if not posts:
            logger.info("No new posts found")
            return

        for vacancy_text, screenshot in posts.items():
            self._process_single_post(vacancy_text, screenshot)

        # self._notify_unsent_vacancies()

    def _process_single_post(self, vacancy_text: str, screenshot: bytes):
        """Process a single LinkedIn post"""
        vacancy_data = self._gpt_processor.analyze_vacancy(vacancy_text)
        screenshot_path = self._generate_screenshot_path()

        if self.repo.create_entry(vacancy_data, screenshot_path, vacancy_text):
            save_screenshot(screenshot_path, screenshot)
            logger.debug(f"Saved screenshot: {screenshot_path}")

    def _generate_screenshot_path(self) -> str:
        """Generate unique screenshot path"""
        return os.path.join("screenshots", f"{datetime.now().timestamp()}.png")


if __name__ == "__main__":
    bot = LinkedInProcessor()
    bot.process_posts()
