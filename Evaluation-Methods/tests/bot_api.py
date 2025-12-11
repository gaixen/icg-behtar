import logging

import google.generativeai as genai
from settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatbotAPI:
    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")

    def get_response(self, prompt_text, system_prompt=None, context_snippets=None):
        try:
            full_prompt = []
            if system_prompt:
                full_prompt.append(system_prompt)
            if context_snippets:
                full_prompt.extend(context_snippets)
            full_prompt.append(prompt_text)

            response = self.model.generate_content(" ".join(full_prompt))
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise ConnectionError("Failed to get response from Gemini API.") from e
