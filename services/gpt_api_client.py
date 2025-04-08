import logging

import requests

from config import GPT4FREE_HOST

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
        self.text_model = "o3-mini"  # Default text model
        self.image_model = "default-image-model"  # Default image model

    def rotate_text_model(self):
        """
        Rotates the text model among a predefined set of models.
        """
        if self.text_model == "o3-mini":
            self.text_model = "deepseek-r1"
        elif self.text_model == "deepseek-r1":
            self.text_model = "gpt-4o-mini"
        elif self.text_model == "gpt-4o-mini":
            self.text_model = "claude-3.7-sonnet"
        elif self.text_model == "claude-3.7-sonnet":
            self.text_model = "gpt-4"
        else:
            self.text_model = "o3-mini"

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
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        # Try up to 3 times, rotating the text model on each failure.
        for _ in range(3):
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

    def get_image(self, prompt: str) -> str:
        """
        Generate an image URL based on the provided prompt.

        Args:
            prompt (str): The input prompt for image generation.

        Returns:
            str: The URL of the generated image or an error message on failure.
        """
        url = f"{self.base_url}/images/generate"
        payload = {
            "prompt": prompt,
            "model": self.image_model,
            "response_format": "url",  # Can be changed to "b64_json" if needed
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()["data"][0]["url"]
        except requests.exceptions.RequestException as err:
            logger.error("Request error in get_image: %s", str(err))
            return f"Error: {str(err)}"
