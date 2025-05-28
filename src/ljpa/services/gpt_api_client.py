import logging

import requests
from utilities.config import PERPLEXITY_API_KEY

COST_THRESHOLD = 0.5

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GPTResponseFormatError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class GPTApiClient:
    def __init__(self, model: str = "sonar"):
        self.base_url = "https://api.perplexity.ai"
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }

        self.model_pricing = {
            "sonar-deep-research": {"input": 5.0, "output": 5.0},
            "sonar-reasoning-pro": {"input": 3.0, "output": 3.0},
            "sonar-reasoning": {"input": 1.0, "output": 1.0},
            "sonar-pro": {"input": 1.0, "output": 1.0},
            "sonar": {"input": 0.2, "output": 0.2},
            "r1-1776": {"input": 2.0, "output": 2.0},
        }

    def count_tokens(self, text: str) -> int:
        try:
            encoder = tiktoken.get_encoding("cl100k_base")
            return len(encoder.encode(text))
        except Exception:
            return len(text) // 4

    def estimate_cost(self, prompt: str, expected_output: int = 150) -> float:
        input_tokens = self.count_tokens(prompt) + self.count_tokens(
            "You are a helpful assistant."
        )
        pricing = self.model_pricing.get(self.model, {"input": 1.0, "output": 1.0})

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (expected_output / 1_000_000) * pricing["output"]

        if "deep-research" in self.model:
            input_cost *= 10
        elif "reasoning" in self.model:
            input_cost *= 5

        return input_cost + output_cost

    def get_text(self, prompt: str, expected_output: int = 150) -> str:
        cost = self.estimate_cost(prompt, expected_output)

        if cost > COST_THRESHOLD:
            raise InsufficientFundsError(
                f"Cost ${cost:.6f} exceeds threshold ${COST_THRESHOLD}"
            )

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