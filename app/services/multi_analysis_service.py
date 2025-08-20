# app/services/analysis_service.py
from openai import AsyncOpenAI  # Note: Async client
from openai import OpenAI
from app.services.multi_persona_services import multi_persona_services

class Multi_AnalysisService:
    def __init__(self):
        self.client = OpenAI(api_key='OPEN_API_KEY')
    async def analyze(self, document_text: str, persona_name: str) -> dict:
        persona = multi_persona_services.get_by_name(persona_name)
        if not persona:
            raise ValueError(f"Persona '{persona_name}' not found")

        system_prompt = persona["system_prompt"]

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": document_text}
            ],
            temperature=0.7
        )

        return {
            "persona": persona_name,
            "feedback": response.choices[0].message.content
        }

multi_analysis_service = Multi_AnalysisService()
