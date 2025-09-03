# app/services/analysis_service.py
from openai import AsyncOpenAI  # Note: Async client
from openai import OpenAI
from app.services.multi_persona_services import multi_persona_services
import os 
import os
import re
import requests
from openai import OpenAI
from app.config import OPENAI_API_KEY

class Multi_AnalysisService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
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

    def extract_dois(self, text: str):
        doi_pattern = r"10\.\d{4,9}/[-._;()/:A-Z0-9]+"
        return re.findall(doi_pattern, text, flags=re.I)

    def extract_references(self, text: str):
        """
        Loosely capture reference-like lines:
        - Start with capital letter
        - Contain year in parentheses
        - Are 50–300 chars long
        """
        refs = []
        for line in text.split("\n"):
            line = line.strip()
            if 50 < len(line) < 300 and re.search(r"\(\d{4}\)", line):
                refs.append(line)
        return refs

    def verify_doi_crossref(self, doi: str):
        url = f"https://api.crossref.org/works/{doi}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json().get("message", {})
                return {
                    "doi": doi,
                    "title": data.get("title", [""])[0],
                    "authors": [
                        f"{a.get('family', '')}, {a.get('given', '')}"
                        for a in data.get("author", [])
                    ],
                    "published": data.get("published-print", {}).get("date-parts", [[]])[0],
                    "source": "CrossRef",
                    "valid": True
                }
        except Exception:
            pass
        return None

    def search_crossref_by_title(self, title: str):
        """Fallback: search CrossRef by title when DOI missing."""
        url = "https://api.crossref.org/works"
        try:
            response = requests.get(url, params={"query.title": title, "rows": 1}, timeout=5)
            if response.status_code == 200:
                items = response.json().get("message", {}).get("items", [])
                if items:
                    item = items[0]
                    return {
                        "doi": item.get("DOI", ""),
                        "title": item.get("title", [""])[0],
                        "authors": [
                            f"{a.get('family', '')}, {a.get('given', '')}"
                            for a in item.get("author", [])
                        ] if "author" in item else [],
                        "published": item.get("issued", {}).get("date-parts", [[]])[0],
                        "source": "CrossRef",
                        "valid": True
                    }
        except Exception:
            pass
        return None

multi_analysis_service = Multi_AnalysisService()
