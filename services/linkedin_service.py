import logging
import os
from datetime import datetime

from services.telemessage import TelegramNotifier

from database.repository import TextEntryRepository
from services.gpt_processor import GPTProcessor
from services.linkedin_scraper import start_linkedin_scraper
from utilities.file_handler import save_screenshot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInBot:
    """
    Service class for processing LinkedIn posts and notifying via Telegram.
    It handles scraping posts, analyzing vacancy data, persisting records, and sending notifications.
    """

    def __init__(self):
        self.repo = TextEntryRepository()
        self.processor = GPTProcessor()
        self.notifier = TelegramNotifier()

    def process_posts(self) -> None:
        """
        Main workflow for processing LinkedIn posts.
        Scrapes new posts, processes each vacancy, and sends notifications for unsent vacancies.
        """
        posts = start_linkedin_scraper()
        if not posts:
            logger.info("No new posts found.")
            return

        for vacancy_text, screenshot in posts.items():
            self._process_single_post(vacancy_text, screenshot)

        self._notify_unsent_vacancies()

    def _process_single_post(self, vacancy_text: str, screenshot: bytes) -> None:
        """
        Processes a single LinkedIn post: analyzes it with GPT, saves a screenshot,
        and creates a new entry in the repository.

        Args:
            vacancy_text (str): The text content of the vacancy.
            screenshot (bytes): Screenshot image in PNG format.
        """
        vacancy_data = self.processor.analyze_vacancy(vacancy_text)
        screenshot_path = self._generate_screenshot_path()

        if self.repo.create_entry(vacancy_data, screenshot_path, vacancy_text):
            save_screenshot(screenshot_path, screenshot)
            logger.debug("Saved screenshot to %s", screenshot_path)

    def _generate_screenshot_path(self) -> str:
        """
        Generates a unique screenshot path using the current timestamp.

        Returns:
            str: The generated screenshot file path.
        """
        return os.path.join("screenshots", f"{datetime.now().timestamp()}.png")

    def _notify_unsent_vacancies(self) -> None:
        """
        Notifies unsent vacancies via Telegram and marks them as sent in the repository.
        """
        unsent_vacancies = self.repo.get_unsent_vacancies()
        for vacancy in unsent_vacancies:
            self._send_vacancy_notification(vacancy)
            self.repo.mark_as_sent(vacancy)

    def _send_vacancy_notification(self, vacancy) -> None:
        """
        Sends a notification for a single vacancy.
        Uses image-based caption and a message generated by the GPT processor.

        Args:
            vacancy: Vacancy record, typically containing attributes like 'vacancy_title',
                     'cv_match', 'visa_sponsorship', 'credentials', 'content', and 'screenshot_path'.
        """
        try:
            caption = self._prepare_caption(vacancy)
            description = self.processor.generate_description(vacancy.content)
            self.notifier.send_image(vacancy.screenshot_path, caption)
            self.notifier.send_message(description)
        except Exception as e:
            logger.error("Notification failed: %s", e)

    def _prepare_caption(self, vacancy) -> str:
        """
        Prepares the caption text for Telegram notifications based on vacancy attributes.

        Args:
            vacancy: Vacancy record containing relevant attributes.

        Returns:
            str: Formatted caption text.
        """
        return (
            f"Vacancy: {vacancy.vacancy_title}\n"
            f"CV Match: {vacancy.cv_match}\n"
            f"Visa Sponsorship: {vacancy.visa_sponsorship}\n"
            f"Credentials: {vacancy.credentials}"
        )


if __name__ == "__main__":
    bot = LinkedInBot()
    bot.process_posts()
