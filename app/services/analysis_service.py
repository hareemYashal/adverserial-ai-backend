import os
import re
import requests
from fuzzywuzzy import fuzz
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

            # No DOI, try CrossRef title search with fuzzy matching
            result = self._search_crossref_by_title(ref)
            match_found = False
            if result and result.get("title"):
                # --- Robust fuzzy matching ---
                import string
                def normalize(text):
                    return ''.join([c for c in text.lower() if c not in string.punctuation]).strip()
                ref_norm = normalize(ref)
                title_norm = normalize(result["title"])
                ratio = fuzz.ratio(title_norm, ref_norm)
                partial = fuzz.partial_ratio(title_norm, ref_norm)
                token_sort = fuzz.token_sort_ratio(title_norm, ref_norm)
                token_set = fuzz.token_set_ratio(title_norm, ref_norm)
                # Accept if any metric is high enough
                if (
                    ratio > 80 or
                    partial > 85 or
                    token_sort > 85 or
                    token_set > 90 or
                    (title_norm in ref_norm and len(title_norm) > 10) or
                    (ref_norm in title_norm and len(ref_norm) > 10)
                ) and title_norm not in seen_titles:
                    verified_citations.append(result)
                    seen_titles.add(title_norm)
                    match_found = True
            if not match_found:
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

    def _search_crossref_by_title(self, ref_title: str):
        """Improved: search CrossRef by title with fuzzy + author matching."""
        import re
        url = "https://api.crossref.org/works"

        def normalize(text):
            return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', text.lower())).strip()

        try:
            response = requests.get(url, params={"query.title": ref_title, "rows": 5}, timeout=5)
            if response.status_code != 200:
                return None

            items = response.json().get("message", {}).get("items", [])
            if not items:
                return None

            ref_norm = normalize(ref_title)
            best_item, best_score = None, 0

            for item in items:
                title = item.get("title", [""])[0]
                title_norm = normalize(title)

                score = max(
                    fuzz.ratio(ref_norm, title_norm),
                    fuzz.partial_ratio(ref_norm, title_norm),
                    fuzz.token_set_ratio(ref_norm, title_norm)
                )

                # Small boost if any author's surname appears in ref
                if "author" in item:
                    authors = [a.get("family", "").lower() for a in item.get("author", [])]
                    if any(a and a in ref_norm for a in authors):
                        score += 5

                if score > best_score:
                    best_score, best_item = score, item

            # Only accept if similarity high enough
            if best_item and best_score >= 70:
                return {
                    "doi": best_item.get("DOI", ""),
                    "title": best_item.get("title", [""])[0],
                    "authors": [
                        f"{a.get('family', '')}, {a.get('given', '')}"
                        for a in best_item.get("author", [])
                    ] if "author" in best_item else [],
                    "published": best_item.get("issued", {}).get("date-parts", [[]])[0],
                    "source": "CrossRef",
                    "valid": True
                }

        except Exception:
            pass

        return None  # fallback → Unverified


# Singleton
analysis_service = AnalysisService()
