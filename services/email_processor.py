import logging
import re

from config import (
    COVER_LETTER_PROMPT,
    CV_FILE_PATH_PDF,
    SMTP_EMAIL,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SERVER,
)
from database_setup import TextEntry  # Model for vacancy entries
from services.smtp_client import SMTPClient  # Renamed SMTPSender to SMTPClient
from services.gpt_api_client import GPTApiClient  # Renamed GPT4FreeInteraction to GPTApiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailProcessor:
    """
    Processes vacancy applications by extracting recipient emails from vacancy posts,
    generating cover letters via GPT, and sending applications via SMTP.
    """

    def __init__(self) -> None:
        self.gpt_api = GPTApiClient()
        self.processed_emails = set()
        self.smtp_config = {
            "email": SMTP_EMAIL,
            "password": SMTP_PASSWORD,
            "smtp_server": SMTP_SERVER,
            "smtp_port": SMTP_PORT,
        }

    def process_vacancies(self) -> None:
        """
        Processes eligible vacancies:
         - Extracts a valid email address
         - Generates a cover letter
         - Sends an application email with the applicant's CV attached.
        """
        for vacancy in self.get_eligible_vacancies():
            email = self.extract_valid_email(vacancy)
            if not email:
                continue
            self.send_application(email, vacancy.vacancy_title, vacancy.content)
            vacancy.spare1 = "Applied"
            vacancy.save()
            logger.info("Marked vacancy '%s' as applied.", vacancy.vacancy_title)

    def get_eligible_vacancies(self):
        """
        Retrieves vacancies eligible for application.
        Eligibility conditions:
          - 'visa_sponsorship' is "available"
          - Vacancy has not been applied to before (spare1 != "Applied")
          - cv_match percentage (numeric) is greater than 40
        """
        eligible = []
        query = TextEntry.select().where(TextEntry.visa_sponsorship == "available")
        for vacancy in query:
            logger.info("Evaluating vacancy: %s", vacancy.vacancy_title)
            try:
                numeric_match = int(vacancy.cv_match.replace("%", "").strip())
            except (ValueError, AttributeError):
                continue  # Skip vacancies with invalid cv_match data
            if vacancy.spare1 == "Applied":
                logger.info("Already applied to: %s", vacancy.vacancy_title)
                continue
            if numeric_match > 40:
                eligible.append(vacancy)
        return eligible

    def extract_email(self, text: str) -> str:
        """
        Extracts the first valid email address from the provided text.
        Raises:
            ValueError: If no email address is found.
        """
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(email_pattern, text)
        if match:
            return match.group(0)
        raise ValueError("No email found in the provided text")

    def extract_valid_email(self, vacancy) -> str:
        """
        Extracts a valid email from a vacancy's content.
        Ensures that each email is processed only once.

        Returns:
            str: The extracted email address, or None if no valid email found.
        """
        try:
            email = self.extract_email(vacancy.content)
            if email in self.processed_emails:
                return None
            self.processed_emails.add(email)
            logger.info("Extracted email: %s", email)
            return email
        except ValueError:
            logger.warning("No email found in vacancy: %s", vacancy.vacancy_title)
            return None

    def send_application(self, recipient_email: str, title: str, content: str) -> None:
        """
        Sends an application email for a vacancy.

        Parameters:
            recipient_email (str): The email address to send the application to.
            title (str): The vacancy title used as the email subject.
            content (str): The vacancy content used to generate the cover letter.
        """
        subject = title
        # Generate cover letter using GPT API client.
        gpt_request = COVER_LETTER_PROMPT + f"\nJob Description: [{content}]"
        message = self.gpt_api.get_text(gpt_request)
        logger.info("Preparing application for vacancy: %s", title)
        logger.debug("Subject: %s | Message: %s", subject, message)

        # Sending email via SMTP client.
        with SMTPClient(self.smtp_config) as smtp_client:
            smtp_client.send_message(recipient_email, subject, message, CV_FILE_PATH_PDF)

        logger.info("Application email sent successfully to %s", recipient_email)


if __name__ == "__main__":
    processor = EmailProcessor()
    processor.process_vacancies()
