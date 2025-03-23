import logging

from database.repository import TextEntryRepository
from services.gpt_processor import GPTProcessor
from services.telemessage import TelegramNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramProcessor:
    def __init__(self):
        self.repo = TextEntryRepository()
        self._gpt_processor = GPTProcessor()
        self.notifier = TelegramNotifier()

    def notify_unsent_vacancies(self):
        for vacancy in self.repo.get_unsent_vacancies():
            self._send_vacancy_notification(vacancy)
            self.repo.mark_as_sent(vacancy)

    def _send_vacancy_notification(self, vacancy):
        """Send Telegram notification for a single vacancy"""
        try:
            caption = self._prepare_caption(vacancy)
            description = self._gpt_processor.generate_description(vacancy.content)

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
