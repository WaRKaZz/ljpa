import logging
from datetime import datetime

from peewee import DoesNotExist

from .database_setup import TextEntry

logger = logging.getLogger(__name__)


class TextEntryRepository:
    def create_entry(self, data: dict, screenshot_path: str, content: str) -> bool:
        if data.get("vacancy") != "true":
            logger.info("Skipping non-vacancy post")
            return False

        try:
            TextEntry.get(TextEntry.content == content)
            logger.debug("Duplicate post found")
            return False
        except DoesNotExist:
            self._create_new_entry(data, screenshot_path, content)
            return True

    def _create_new_entry(self, data: dict, screenshot_path: str, content: str):
        TextEntry.create(
            content=content,
            screenshot_path=screenshot_path,
            cv_match=data.get("cv_match"),
            vacancy_title=data.get("vacancy_title"),
            credentials=data.get("credentials"),
            visa_sponsorship=data.get("visa_sponsorship"),
            sent="False",
            deleted=False,
            created_date=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        )
        logger.info("New vacancy stored")

    def get_unsent_vacancies(self):
        return TextEntry.select().where(
            (TextEntry.sent == "False") & (TextEntry.deleted == False)
        )

    def mark_as_sent(self, vacancy):
        vacancy.sent = "True"
        vacancy.save()
