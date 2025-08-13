from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.services.persona_services import persona_service

class AnalysisService:
    def __init__(self):
        self.client = OpenAI(api_key='OPEN_API_KEY')
        # If you want to hardcode, you can still do:
        # self.client = OpenAI(api_key='sk-proj-...')

    def analyze(self, document_text: str, persona_name: str) -> str:
        persona = persona_service.get_by_name(persona_name)
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

        # FIX: use attribute access instead of dict indexing
        return response.choices[0].message.content

analysis_service = AnalysisService()
