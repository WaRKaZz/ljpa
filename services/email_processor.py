import logging
import re

from consts import (
    COVER_LETTER_PROMPT,
    CV_FILE_PATH_PDF,
    EMAIL_SIGNATURE,
    SMTP_EMAIL,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SERVER,
)
from database_setup import TextEntry
from services.email import SMTPSender
from services.GPT_API import GPT4FreeInteraction

logging.basicConfig(level=logging.INFO)


class EmailProcessor:
    def __init__(self):
        self.gpt_api = GPT4FreeInteraction()
        self.applied_emails = set()
        self.smtp_config = {
            "email": SMTP_EMAIL,
            "password": SMTP_PASSWORD,
            "smtp_server": SMTP_SERVER,
            "smtp_port": SMTP_PORT,
        }

    def process_vacancies(self):
        for vacancy in self.get_eligible_vacancies():
            email = self.extract_valid_email(vacancy)
            if not email:
                continue
            self.send_application(email, vacancy.vacancy_title, vacancy.content)
            vacancy.spare1 = "Applied"
            vacancy.save()

    def get_eligible_vacancies(self):
        eligible = []
        for vacancy in TextEntry.select().where(
            TextEntry.visa_sponsorship == "available"
        ):
            logging.info(f"Trying to apply {vacancy.vacancy_title}")
            cv_value = vacancy.cv_match
            cleaned = cv_value.replace("%", "").strip()
            try:
                numeric_value = int(cleaned)
            except ValueError:
                continue  # Skip non-numeric entries
            if vacancy.spare1 == "Applied":
                logging.info("Already applied: %s", vacancy.vacancy_title)
                continue
            if numeric_value > 40:
                eligible.append(vacancy)
        return eligible

    def extract_email(self, text: str) -> str:
        """Extracts the first email from a string. Raises ValueError if no email is found."""
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(email_pattern, text)
        if match:
            return match.group(0)
        raise ValueError("No email found in the provided text")

    def extract_valid_email(self, vacancy):
        try:
            email = self.extract_email(vacancy.content)
            if email in self.applied_emails:
                return None
            self.applied_emails.add(email)
            logging.info("Extracted email: %s", email)
            return email
        except ValueError:
            logging.warning("No email found in: %s", vacancy.vacancy_title)
            return None

    def send_application(self, email, title, content):
        subject = title
        GPT_REQUEST = COVER_LETTER_PROMPT + f"\nJob Description: [{content}]"
        message = self.gpt_api.get_text(GPT_REQUEST)
        print(f"Subject: {subject} \nMessage: {message}")
        with SMTPSender(self.smtp_config) as sender:
            sender.send_message(email, subject, message, CV_FILE_PATH_PDF)
        logging.info("Email sent successfully to %s", email)


if __name__ == "__main__":
    processor = EmailProcessor()
    processor.process_vacancies()
