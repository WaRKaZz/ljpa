import logging

import requests

from utilities.config import G4FREE_PROVIDER, GPT4FREE_HOST

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GPTResponseFormatError(Exception):
    """
    Custom exception for GPT API response format errors.
    """

    pass


class GPTApiClient:
    """
    Client for interacting with the GPT4Free API service.

    Provides methods for generating text and images based on input prompts.
    """

    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = f"http://{GPT4FREE_HOST}:1337/v1"
        self.base_url = base_url
        self._index = 0
        self.text_models = self._get_text_models()
        self.text_model = self.text_models[self._index]

    def rotate_text_model(self):
        """
        Rotates the text model among a predefined set of models.
        """
        self._index = (self._index + 1) % len(self.text_models)
        self.model = self.text_models[self._index]

    def get_text(self, prompt: str) -> str:
        """
        Generate text based on the provided prompt by switching models on errors.

        Args:
            prompt (str): The user prompt for text generation.

        Returns:
            str: The generated text or an error message if all attempts fail.
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.text_model,
            "provider": G4FREE_PROVIDER,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        # Try all text models, rotating the text model on each failure.
        for _ in range(len(self.text_models) - 1):
            self.rotate_text_model()
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                # Assumption: response is expected to follow the GPT API format.
                return response.json()["choices"][0]["message"]["content"]
            except requests.exceptions.RequestException as err:
                logger.error("Request error in get_text: %s", str(err))
                continue
        return "Error: Impossible Situation"

    def _get_text_models(self):
        provider_list_url = f"{self.base_url}/providers/{G4FREE_PROVIDER}"
        response = requests.get(
            provider_list_url, headers={"accept": "application/json"}
        )
        provider_details = response.json()
        return provider_details["models"]
