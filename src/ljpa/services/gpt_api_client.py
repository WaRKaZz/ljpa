import logging
import requests
from utilities.config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GPTResponseFormatError(Exception):
    pass


class GPTApiClient:
    def __init__(self, model: str = "meta-llama/llama-4-scout:free"):
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

    def get_text(self, prompt: str, expected_output: int = 150) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as err:
            logger.error("Request error: %s", str(err))
            return "Error: Request failed"
        except (KeyError, IndexError) as err:
            logger.error("Response format error: %s", str(err))
            return "Error: Invalid response format"
