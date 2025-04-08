import logging
import re
import time
from typing import Dict

from consts import RECRUITMENT_PROMPT, TELEGRAM_CLEAR_PROMPT
from services.GPT_API import GPT4FreeInteraction, ResponseFormatError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPTProcessor:
    MAX_RETRIES = 13
    RETRY_DELAY = 5

    def __init__(self):
        self.gpt = GPT4FreeInteraction()
        self.prompt_errors = 0

    def analyze_vacancy(self, text: str) -> dict:
        clean_text = self._sanitize_text(text)
        for attempt in range(self.MAX_RETRIES):
            try:
                GPT_REQUEST = RECRUITMENT_PROMPT + clean_text
                response = self.gpt.get_text(GPT_REQUEST)
                return self._validate_response(response)
            except (ResponseFormatError, KeyError) as e:
                logging.error(f"Failed to process vacancy:\n{e}\nresponce={response}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
        return {"vacancy": "false"}

    def generate_description(self, text: str) -> str:
        GPT_REQUEST = TELEGRAM_CLEAR_PROMPT + text
        return self.gpt.get_text(GPT_REQUEST)

    def _sanitize_text(self, text: str) -> str:
        return text.replace("ivan.danilov.wk@gmail.com", "").replace(
            "+7 701 724 25 32", ""
        )

    def _validate_response(self, response: str) -> dict:
        parsed = self._parse_response(response)
        if parsed.get("vacancy") == "true" and parsed.get("credentials") == "na":
            raise ResponseFormatError("Missing credentials")
        return parsed

    def _parse_response(self, response: str) -> Dict[str, str]:
        """
        Parses GPT response into structured data with validation
        Handles flexible field order and missing optional fields
        """
        if self.prompt_errors >= 2:
            self.gpt.switch_model()

        pattern = r"(\w+):\s*\[([^]]+)\]"
        fields = dict(re.findall(pattern, response.lower()))

        # Required fields
        required = ["vacancy"]
        for field in required:
            if field not in fields:
                self.prompt_errors += 1
                raise ResponseFormatError(f"Missing required field: {field}")

        # Conditional requirements
        if fields.get("vacancy") == "true":
            if "cv_match" not in fields:
                self.prompt_errors += 1
                raise ResponseFormatError("CV match required when vacancy=true")
            try:
                fields["cv_match"] = int(fields["cv_match"].replace("%", ""))
            except ValueError:
                self.prompt_errors += 1
                raise ResponseFormatError("Invalid CV match format")

        # Validate values
        validations = {
            "vacancy": ["true", "false"],
            "visa_sponsorship": [
                "available",
                "unavailable",
                "not available",
                "not mentioned",
                "n/a",
                "n\\a",
                "n-a",
                "none",
            ],
        }

        for field, value in fields.items():
            if field in validations:
                if value.lower() not in validations[field]:
                    self.prompt_errors += 1
                    raise ResponseFormatError(
                        f"Invalid value '{value}' for field {field}"
                    )

        # Map to original case fields
        case_map = {k.lower(): k for k in re.findall(r"(\w+):", response)}
        return {case_map[k]: v for k, v in fields.items()}
