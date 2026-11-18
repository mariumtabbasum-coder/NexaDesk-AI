from config import Config
from google import genai
class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None
    @property
    def available(self):
        return self.client is not None
    def generate(self, prompt):
        if not self.client:
            return "Gemini is not configured yet. Add your GEMINI_API_KEY to the .env file and restart the server."
        try:
            response = self.client.models.generate_content(model=Config.GEMINI_CHAT_MODEL, contents=prompt)
            return response.text or "I couldn't generate a response. Please try again."
        except Exception as exc:
            return f"Gemini request failed: {exc}"
