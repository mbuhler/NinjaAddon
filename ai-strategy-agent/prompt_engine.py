import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from schemas.models import AnalysisResponse
import json

load_dotenv()

class PromptEngine:
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.gemini_api_key)

    def get_analysis(self, prompt: str, provider: str, model: str) -> AnalysisResponse:
        if provider == "openrouter":
            return self._get_openrouter_analysis(prompt, model)
        elif provider == "gemini":
            return self._get_gemini_analysis(prompt, model)
        else:
            raise ValueError("Invalid provider specified.")

    def _get_openrouter_analysis(self, prompt: str, model: str) -> AnalysisResponse:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "HTTP-Referer": "my-app.local",
                "X-Title": "NT-AI-Agent",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        # The line below is a potential bug. The response from the LLM is a string,
        # but it's not guaranteed to be a valid JSON.
        return AnalysisResponse(**json.loads(response.json()["choices"][0]["message"]["content"]))

    def _get_gemini_analysis(self, prompt: str, model: str) -> AnalysisResponse:
        model = genai.GenerativeModel(model)
        response = model.generate_content(prompt)
        return AnalysisResponse(**json.loads(response.text))

    def discover_openrouter_models(self):
        response = requests.get("https://openrouter.ai/api/v1/models")
        response.raise_for_status()
        return response.json()
