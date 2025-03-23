import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os


class SMTPSender:
    def __init__(self, config):
        """
        Initializes SMTP sender with configuration.

        :param config: Dictionary with SMTP settings:
            {
                "email": "your_email@gmail.com",
                "password": "your_password",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587
            }
        """
        self.smtp_server = config["smtp_server"]
        self.smtp_port = config["smtp_port"]
        self.username = config["email"]
        self.password = config["password"]
        self.smtp = None

    def connect(self):
        """Connects to SMTP server."""
        self.smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
        self.smtp.starttls()  # Secure connection
        self.smtp.login(self.username, self.password)

    def disconnect(self):
        """Closes SMTP connection."""
        if self.smtp:
            self.smtp.quit()

    def send_message(self, recipient, subject, message, attachment_path=None):
        """
        Sends an email.

        :param recipient: Recipient email address.
        :param subject: Email subject.
        :param message: Email body text.
        :param attachment_path: Path to attachment file (optional).
        """
        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        # Attach file if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}"
                )
                msg.attach(part)

        # Send email
        self.smtp.sendmail(self.username, recipient, msg.as_string())

    def __enter__(self):
        """Context manager entry: connects to SMTP."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: disconnects from SMTP."""
        self.disconnect()


# Example Usage for Gmail
if __name__ == "__main__":
    config = {
        "email": "your_email@gmail.com",
        "password": "your_password",  # Use App Password if 2FA is enabled
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587
    }

    recipient_email = "recipient@example.com"

    with SMTPSender(config) as sender:
        sender.send_message(
            recipient_email,
            "Test Email",
            "This is a test email via SMTP.",
            "example.txt"
        )
