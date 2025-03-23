import re

from consts import JOB_TITLE_EXTRACTOR_PROMPT
from database_setup import TextEntry
from services.GPT_API import GPT4FreeInteraction


def database_vacancy_title_update():
    gpt_api = GPT4FreeInteraction()
    for vacancy in TextEntry.select().where(TextEntry.vacancy_title == None):
        vacancy_title = gpt_api.get_text(
            system_prompt=JOB_TITLE_EXTRACTOR_PROMPT, prompt=vacancy.content
        )
        print(vacancy_title)
        input("Press Enter to continue... or ctrl+c to abort")
        vacancy.vacancy_title = vacancy_title
        vacancy.save()


def extract_email(text: str) -> str:
    """Extracts the first email from a string. Raises ValueError if no email is found."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(email_pattern, text)
    if match:
        return match.group(0)
    raise ValueError("No email found in the provided text")
