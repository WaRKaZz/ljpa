import logging

from services.email_processor import EmailProcessor
from services.linkedin_processor import LinkedInProcessor
from services.telegram_processor import TelegramProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting linkedin bot")
    linkedin_bot = LinkedInProcessor()
    linkedin_bot.process_posts()
    logger.info("Starting telegram bot")
    telegram_bot = TelegramProcessor()
    telegram_bot.notify_unsent_vacancies()
    logger.info("Starting email processor")
    email_processor = EmailProcessor()
    email_processor.process_vacancies()


if __name__ == "__main__":
    main()
    exit()