import logging
import os
from datetime import datetime

from linkedin import startLinkedinScrapper
from telemessage import TelegramNotifier

from database.repository import TextEntryRepository
from services.gpt_processor import VacancyProcessor
from utilities.file_handler import save_screenshot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInBot:
    def __init__(self):
        self.repo = TextEntryRepository()
        self.processor = VacancyProcessor()
        self.notifier = TelegramNotifier()

    def process_posts(self):
        """Main workflow for processing LinkedIn posts"""
        posts = startLinkedinScrapper()
        if not posts:
            logger.info("No new posts found")
            return

        for vacancy_text, screenshot in posts.items():
            self._process_single_post(vacancy_text, screenshot)

        self._notify_unsent_vacancies()

    def _process_single_post(self, vacancy_text: str, screenshot: bytes):
        """Process a single LinkedIn post"""
        vacancy_data = self.processor.analyze_vacancy(vacancy_text)
        screenshot_path = self._generate_screenshot_path()

        if self.repo.create_entry(vacancy_data, screenshot_path, vacancy_text):
            save_screenshot(screenshot_path, screenshot)
            logger.debug(f"Saved screenshot: {screenshot_path}")

    def _generate_screenshot_path(self) -> str:
        """Generate unique screenshot path"""
        return os.path.join("screenshots", f"{datetime.now().timestamp()}.png")

    def _notify_unsent_vacancies(self):
        """Send notifications for unsent vacancies"""
        for vacancy in self.repo.get_unsent_vacancies():
            self._send_vacancy_notification(vacancy)
            self.repo.mark_as_sent(vacancy)

    def _send_vacancy_notification(self, vacancy):
        """Send Telegram notification for a single vacancy"""
        try:
            caption = self._prepare_caption(vacancy)
            description = self.processor.generate_description(vacancy.content)
            
            self.notifier.send_image(vacancy.screenshot_path, caption)
            self.notifier.send_message(description)
        except Exception as e:
            logger.error(f"Notification failed: {e}")

    def _prepare_caption(self, vacancy) -> str:
        """Prepare image caption for Telegram"""
        return (
            f"Vacancy: {vacancy.vacancy_title}\n"
            f"CV Match: {vacancy.cv_match}\n"
            f"Visa Sponsorship: {vacancy.visa_sponsorship}\n"
            f"Credentials: {vacancy.credentials}"
        )


if __name__ == "__main__":
    bot = LinkedInBot()
    bot.process_posts()