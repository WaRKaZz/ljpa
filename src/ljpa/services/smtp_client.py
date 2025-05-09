import logging
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SMTPClient:
    """
    SMTP client for sending emails with optional attachments.

    Example configuration should include:
        {
            "email": "your_email@example.com",
            "password": "your_password",
            "smtp_server": "smtp.example.com",
            "smtp_port": 587
        }
    """

    def __init__(self, config: dict):
        self.smtp_server = config["smtp_server"]
        self.smtp_port = config["smtp_port"]
        self.username = config["email"]
        self.password = config["password"]
        self.connection = None

    def connect(self):
        """
        Connects to the SMTP server using TLS and logs in with the provided credentials.
        """
        try:
            self.connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.connection.starttls()  # Secure the connection.
            self.connection.login(self.username, self.password)
            logger.info(
                "Connected to SMTP server %s on port %s",
                self.smtp_server,
                self.smtp_port,
            )
        except Exception as e:
            logger.error("Error connecting to SMTP server: %s", e)
            raise

    def disconnect(self):
        """
        Gracefully disconnects from the SMTP server.
        """
        if self.connection:
            self.connection.quit()
            logger.info("Disconnected from SMTP server.")

    def send_message(
        self, recipient: str, subject: str, body: str, attachment_path: str = None
    ):
        """
        Sends an email with an optional attachment.

        Parameters:
            recipient (str): The recipient's email address.
            subject (str): The email subject.
            body (str): The main text body of the email.
            attachment_path (str, optional): File path of the attachment to include.
        """
        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Process attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}",
                )
                msg.attach(part)
                logger.info("Attached file %s", attachment_path)
            except Exception as e:
                logger.error("Failed to attach file %s: %s", attachment_path, e)
                raise

        try:
            self.connection.sendmail(self.username, recipient, msg.as_string())
            logger.info("Email sent to %s", recipient)
        except Exception as e:
            logger.error("Error sending email: %s", e)
            raise

    def __enter__(self):
        """
        Context manager entry. Opens the SMTP connection.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Context manager exit. Closes the SMTP connection.
        """
        self.disconnect()


# Example Usage for Gmail or similar SMTP provider
if __name__ == "__main__":
    config = {
        "email": "your_email@gmail.com",
        "password": "your_password",  # Use App Password if 2FA is enabled
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
    }

    recipient_email = "recipient@example.com"

    with SMTPClient(config) as client:
        client.send_message(
            recipient=recipient_email,
            subject="Test Email",
            body="This is a test email via SMTP.",
            attachment_path="example.txt",
        )
