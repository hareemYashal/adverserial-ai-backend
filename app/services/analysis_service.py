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
        # Step 1: Isolate references section
        references_text = self._get_references_section(document_text)
        # Step 2: Extract and deduplicate references
        refs = self._extract_references(references_text)
        unique_refs = list(dict.fromkeys(refs))

        verified_citations = []
        seen_dois = set()
        seen_titles = set()

        for ref in unique_refs:
            # Extract DOI from this reference only
            ref_dois = self._extract_dois(ref)
            if ref_dois:
                for doi in ref_dois:
                    if doi in seen_dois:
                        continue
                    result = self._verify_doi_crossref(doi)
                    if result:
                        verified_citations.append(result)
                        seen_dois.add(doi)
                        if result.get("title"):
                            seen_titles.add(result["title"].lower())
                continue  # If DOI found, skip title search for this ref

            # No DOI, try strict CrossRef title search
            result = self._search_crossref_by_title(ref)
            # Only accept if returned title is a close match to the reference (case-insensitive substring)
            if result and result.get("title") and result["title"].lower() in ref.lower():
                if result["title"].lower() not in seen_titles:
                    verified_citations.append(result)
                    seen_titles.add(result["title"].lower())
            else:
                # Keep raw if not found or not a close match
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

    def _get_references_section(self, text: str) -> str:
        """
        Extracts the text after the 'References' heading (case-insensitive).
        """
        import re
        match = re.search(r'(?i)\bReferences\b', text)
        if match:
            return text[match.end():].strip()
        return text

    def _extract_dois(self, text: str):
        doi_pattern = r"10\.\d{4,9}/[-._;()/:A-Z0-9]+"
        return re.findall(doi_pattern, text, flags=re.I)

    def _extract_references(self, text: str):
        """
        Extract references as blocks of lines, joining multi-line references.
        Handles both numbered and unnumbered references.
        Assumes input is the references section only.
        """
        import re
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        refs = []
        current_ref = []
        # Pattern for numbered references (e.g., 1. or 12.)
        numbered_pattern = re.compile(r'^(\d{1,3})[.\)]\s+')
        # Pattern for author-year references
        author_year_pattern = re.compile(r'^[A-Z][^\n]*\(\d{4}[a-z]?\)')

        for line in lines:
            is_new_ref = False
            if numbered_pattern.match(line):
                is_new_ref = True
            elif author_year_pattern.match(line):
                is_new_ref = True
            elif not current_ref:
                is_new_ref = True

            if is_new_ref:
                if current_ref:
                    refs.append(' '.join(current_ref))
                    current_ref = []
                current_ref.append(line)
            else:
                # Continuation of previous reference
                if current_ref:
                    current_ref.append(line)
        if current_ref:
            refs.append(' '.join(current_ref))
        # Remove any empty or very short references
        refs = [ref for ref in refs if len(ref) > 10]
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
