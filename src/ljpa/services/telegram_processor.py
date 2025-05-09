import logging
from typing import Any

from db.repository import TextEntryRepository
from services.gpt_processor import GPTProcessor
from services.telemessage import TelegramNotifier

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TelegramProcessor:
    """Processes and sends unsent vacancy notifications via Telegram."""

    def __init__(self) -> None:
        self.repo = TextEntryRepository()
        self.gpt_processor = GPTProcessor()
        self.notifier = TelegramNotifier()

    def notify_unsent_vacancies(self) -> None:
        """Notify all unsent vacancies using Telegram."""
        vacancies = self.repo.get_unsent_vacancies()
        if not vacancies:
            logger.info("No unsent vacancies to notify.")
            return

        logger.info("Notifying %d unsent vacancies...", len(vacancies))

        for vacancy in vacancies:
            success = self._send_vacancy_notification(vacancy)
            if success:
                self.repo.mark_as_sent(vacancy)

    def _send_vacancy_notification(self, vacancy: Any) -> bool:
        """Send a Telegram notification for a single vacancy."""
        try:
            caption = self._prepare_caption(vacancy)
            description = self.gpt_processor.generate_description(vacancy.content)

            self.notifier.send_image(vacancy.screenshot_path, caption)
            self.notifier.send_message(description)

            logger.info("Notification sent for: %s", vacancy.vacancy_title)
            return True
        except Exception as e:
            logger.error("Notification failed for %s: %s", vacancy.vacancy_title, str(e))
            return False

    def _prepare_caption(self, vacancy: Any) -> str:
        """Generate the caption text shown with the Telegram image."""
        return (
            f"Vacancy: {vacancy.vacancy_title}\n"
            f"CV Match: {vacancy.cv_match}\n"
            f"Visa Sponsorship: {vacancy.visa_sponsorship}\n"
            f"Credentials: {vacancy.credentials}"
        )
