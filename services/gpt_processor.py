import logging
import re
import time
from typing import Dict

from config import RECRUITMENT_PROMPT, TELEGRAM_CLEAR_PROMPT
from services.gpt_api_client import GPTApiClient, GPTResponseFormatError

# Configure logging for the module.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPTProcessor:
    """
    Processes vacancy text using the GPT API client:
    - Analyzes vacancy details.
    - Generates cleaned vacancy descriptions for Telegram notifications.
    """
    MAX_RETRIES = 13
    RETRY_DELAY = 5

    def __init__(self) -> None:
        self.gpt: GPTApiClient = GPTApiClient()
        self.prompt_errors = 0

    def analyze_vacancy(self, text: str) -> Dict[str, str]:
        """
        Analyzes vacancy description text using a recruitment prompt and returns structured data.
        
        If the GPT response is invalid or missing required fields, it retries up to MAX_RETRIES times.
        
        Args:
            text (str): The vacancy description text.
        
        Returns:
            dict: Parsed vacancy data, or {"vacancy": "false"} if processing fails.
        """
        clean_text = self._sanitize_text(text)
        for attempt in range(self.MAX_RETRIES):
            try:
                gpt_request = f"{RECRUITMENT_PROMPT}{clean_text}"
                response = self.gpt.get_text(gpt_request)
                return self._validate_response(response)
            except (GPTResponseFormatError, KeyError) as e:
                logger.error("Attempt %d: Failed to process vacancy. Error: %s. Response: %s", 
                             attempt + 1, e, response if 'response' in locals() else "N/A")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
        return {"vacancy": "false"}

    def generate_description(self, text: str) -> str:
        """
        Generates a refined description for vacancy posts using the Telegram clear prompt.
        
        Args:
            text (str): The original vacancy content.
        
        Returns:
            str: Refined vacancy description.
        """
        gpt_request = f"{TELEGRAM_CLEAR_PROMPT}{text}"
        return self.gpt.get_text(gpt_request)

    def _sanitize_text(self, text: str) -> str:
        """
        Cleans the vacancy text by removing unwanted contact information.
        
        Args:
            text (str): The raw vacancy text.
        
        Returns:
            str: The sanitized vacancy text.
        """
        # Remove specific email and phone data.
        return text.replace("ivan.danilov.wk@gmail.com", "").replace("+7 701 724 25 32", "")

    def _validate_response(self, response: str) -> Dict[str, str]:
        """
        Validates and parses the GPT response.
        
        Raises:
            GPTResponseFormatError: If required fields are missing or improperly formatted.
        
        Args:
            response (str): The raw response from the GPT API.
        
        Returns:
            dict: The parsed response as a dictionary.
        """
        parsed = self._parse_response(response)
        # Check if vacancy is true and credentials are missing.
        if parsed.get("vacancy") == "true" and parsed.get("credentials") == "na":
            raise GPTResponseFormatError("Missing credentials")
        return parsed

    def _parse_response(self, response: str) -> Dict[str, str]:
        """
        Parses the GPT response into a dictionary of field/value pairs.
        
        The expected response format is fields formatted as:
            field: [value]
        irrespective of field order and allowing for some optional fields.
        
        Args:
            response (str): The raw GPT response.
        
        Raises:
            GPTResponseFormatError: If required fields are missing or if validation fails.
        
        Returns:
            dict: Dictionary with parsed field values.
        """
        # Switch model if repeated errors occur.
        if self.prompt_errors >= 2:
            self.gpt.rotate_text_model()

        # Pattern for fields in the format: key: [value]
        pattern = r"(\w+):\s*\[([^]]+)\]"
        fields = dict(re.findall(pattern, response.lower()))

        # Ensure required fields are present.
        for required_field in ["vacancy"]:
            if required_field not in fields:
                self.prompt_errors += 1
                raise GPTResponseFormatError(f"Missing required field: {required_field}")

        # For vacancies that are marked true, ensure cv_match is present and valid.
        if fields.get("vacancy") == "true":
            if "cv_match" not in fields:
                self.prompt_errors += 1
                raise GPTResponseFormatError("CV match required when vacancy=true")
            try:
                fields["cv_match"] = int(fields["cv_match"].replace("%", ""))
            except ValueError:
                self.prompt_errors += 1
                raise GPTResponseFormatError("Invalid CV match format")

        # Validate fields with expected values.
        validations = {
            "vacancy": {"true", "false"},
            "visa_sponsorship": {"available", "unavailable", "not available", "not mentioned", "n/a", "n\\a", "n-a", "none"},
        }
        for field, value in fields.items():
            if field in validations and value.lower() not in validations[field]:
                self.prompt_errors += 1
                raise GPTResponseFormatError(f"Invalid value '{value}' for field {field}")

        # Remap keys to maintain original case based on the response.
        original_keys = re.findall(r"(\w+):", response)
        case_map = {k.lower(): k for k in original_keys}
        return {case_map.get(k, k): v for k, v in fields.items()}
