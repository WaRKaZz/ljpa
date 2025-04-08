import requests

from consts import GPT4FREE_HOST


class ResponseFormatError(Exception):
    """Custom exception for format errors"""

    pass


class GPT4FreeInteraction:
    def __init__(self, base_url=f"http://{GPT4FREE_HOST}:1337/v1"):
        self.base_url = base_url
        self.text_model = "o3-mini"  # Default text model

    def switch_model(self):
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

    def get_text(self, prompt):
        """
        Generate text based on the user's prompt.
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
        for i in range(3):
            self.switch_model()
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except requests.exceptions.RequestException as e:
                print(f"Error: {str(e)}")
                continue
        return f"Error: Impossible Situation"

    def get_image(self, prompt):
        """
        Generate an image based on the user's prompt.
        """
        url = f"{self.base_url}/images/generate"
        payload = {
            "prompt": prompt,
            "model": self.image_model,
            "response_format": "url",  # Can be changed to "b64_json"
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()["data"][0]["url"]
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"
