import os
import re
import requests
from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.services.persona_services import persona_service


class AnalysisService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY)
        self.client = OpenAI(api_key=api_key)

    def analyze(self, document_text: str, persona_name: str) -> dict:
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

        llm_output = response.choices[0].message.content

        # --- Extract citations ---
        dois = self._extract_dois(document_text)
        refs = self._extract_references(document_text)

        verified_citations = []

        # 1. Verify DOIs against CrossRef
        for doi in dois:
            result = self._verify_doi_crossref(doi)
            if result:
                verified_citations.append(result)

        # 2. For non-DOI refs, try CrossRef title search
        for ref in refs:
            if any(doi in ref for doi in dois):
                continue  # already handled
            result = self._search_crossref_by_title(ref)
            if result:
                verified_citations.append(result)
            else:
                # Keep raw if not found
                verified_citations.append({
                    "title": ref,
                    "source": "Unverified",
                    "valid": False
                })

        return {
            "persona": persona_name,
            "feedback": {
                "analysis": llm_output,
                "citations": verified_citations
            }
        }

    def _extract_dois(self, text: str):
        doi_pattern = r"10\.\d{4,9}/[-._;()/:A-Z0-9]+"
        return re.findall(doi_pattern, text, flags=re.I)

    def _extract_references(self, text: str):
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

    def _verify_doi_crossref(self, doi: str):
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

    def _search_crossref_by_title(self, title: str):
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


# Singleton
analysis_service = AnalysisService()
