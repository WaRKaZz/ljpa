import logging

from services.email_processor import EmailProcessor
from services.linkedin_service import LinkedInBot
from services.telegram_processor import TelegramProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting LinkedIn automation bot...")

    try:
        bot = LinkedInBot()
        bot.process_posts()

        emailer = EmailProcessor()
        emailer.process_vacancies()

        telegram = TelegramProcessor()
        telegram.notify_unsent_vacancies()

        logger.info("Process completed successfully.")
    except Exception as e:
        logger.exception(f"Unexpected error occurred during execution: {e}")


if __name__ == "__main__":
    main()
