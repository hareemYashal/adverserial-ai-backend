# app/services/multi_analysis_service.py
import os
import re
import json
import requests
from openai import AsyncOpenAI
from openai import OpenAI
from app.services.multi_persona_services import multi_persona_services
from app.config import OPENAI_API_KEY
from fuzzywuzzy import fuzz

class Multi_AnalysisService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY)
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
    
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
        llm_output = response.choices[0].message.content

        # Extract references section and parse with LLM
        references_text = self._get_references_section(document_text)
        citations_json = self.extract_citations_llm(references_text)

        # Verify citations using the improved method
        verified_citations = self.verify_citations_improved(references_text, citations_json["citations"])

        return {
            "persona": persona_name,
            "feedback": {
                "analysis": llm_output,
                "citations": verified_citations
            }
        }

    def extract_citations_llm(self, references_text: str) -> dict:
        """
        Extracts references section and parses citations into strict JSON.
        """
        PROMPT = """
You are a meticulous, rule-following bibliographic parser. 
Your job is ONLY to parse the REFERENCES/BIBLIOGRAPHY text provided and return a strict JSON object — nothing else.

Extract every bibliographic reference and return ONLY valid JSON. 
The JSON must be a single object with key "citations", whose value is a list of citation objects in the same order they appear.

Each citation object MUST contain exactly these fields in this order:
1. "title" (string) — title of the work (include subtitles only).
2. "authors" (array of strings) — list of authors exactly as in the reference (e.g., ["Smith, J.", "Doe, A."]). Remove roles like (Eds.), (Trans.).
3. "published" (array) — a single-element array with the year as integer, e.g. [1998].
4. "id" (integer) — a running index starting at 1.
5. "doi" — always null at extraction stage.
6. "verified" (boolean) — always false at extraction stage.

Rules: 
- RETURN ONLY JSON. No commentary, no extra text, no markdown fences. 
- DO NOT invent data. Extract only from provided text. 
- Identify reference boundaries by "Author(s), YEAR". Capture wrapped lines until the next author-year or end of block. 
- For published date: take the first 4-digit year inside parentheses after authors.
- For title: extract the sentence immediately after the year period. Stop before publisher/journal info. 
- Exclude DOIs, URLs, page numbers, publisher, and editors from the title.

OUTPUT FORMAT EXAMPLE:
{
  "citations": [
    {
      "title": "Lenin and philosophy and other essays",
      "authors": ["Althusser, L."],
      "published": [1971],
      "id": 1,
      "doi": null,
      "verified": false
    },
    {
      "title": "To-do is to be: Foucault, Levinas, and technologically mediated subjectivation",
      "authors": ["Bergen, J. P.", "Verbeek, P.-P."],
      "published": [2021],
      "id": 2,
      "doi": null,
      "verified": false
    }
  ]
}

TEXT:
<<<REFERENCES_TEXT>>>
"""

        prompt = PROMPT.replace("<<<REFERENCES_TEXT>>>", references_text[:150000])

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a JSON-only extractor for bibliographic references."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=3000,
        )

        text_out = response.choices[0].message.content.strip()

        # Safe JSON parse
        def safe_parse_json(maybe_json: str):
            maybe_json = maybe_json.strip()
            try:
                return json.loads(maybe_json)
            except Exception:
                m = re.search(r"(\{(?:.|\n)*\})", maybe_json)
                if m:
                    try:
                        return json.loads(m.group(1))
                    except Exception:
                        pass
            raise ValueError("Could not parse JSON from model output")

        parsed = safe_parse_json(text_out)
        return parsed

    def verify_citations_improved(self, references_text: str, citations: list) -> list:
        """
        Improved verification using the approach from the working script.
        First try to extract DOIs from the raw references text, then fall back to title search.
        """

        # Extract raw references from the text
        raw_refs = self._extract_references(references_text)
        unique_refs = list(dict.fromkeys(raw_refs))
        
        verified_citations = []
        seen_dois = set()
        seen_titles = set()

        # Map each citation to its raw reference text
        citation_to_raw = {}
        for i, citation in enumerate(citations):
            if i < len(unique_refs):
                citation_to_raw[citation["id"]] = unique_refs[i]
            else:
                # Fallback: use title + authors + year to reconstruct
                authors_str = " ".join(citation.get("authors", []))
                year_str = str(citation.get("published", [""])[0])
                citation_to_raw[citation["id"]] = f"{authors_str} ({year_str}) {citation.get('title', '')}"

        # Verify each citation
        for citation in citations:
            raw_ref = citation_to_raw.get(citation["id"], "")
            
            # Step 1: Try to extract DOI from raw reference
            ref_dois = self._extract_dois(raw_ref)
            doi_found = False
            
            if ref_dois:
                for doi in ref_dois:
                    if doi in seen_dois:
                        continue
                    result = self._verify_doi_crossref(doi)
                    if result:
                        # Update citation with verified data
                        citation["doi"] = doi
                        citation["verified"] = True
                        if result.get("title") and not citation.get("title"):
                            citation["title"] = result["title"]
                        if result.get("authors") and not citation.get("authors"):
                            citation["authors"] = result["authors"]
                        if result.get("published") and not citation.get("published"):
                            citation["published"] = result["published"]
                            
                        verified_citations.append(citation)
                        seen_dois.add(doi)
                        if citation.get("title"):
                            seen_titles.add(citation["title"].lower())
                        doi_found = True
                        break
            
            if doi_found:
                continue  # Skip to next citation if DOI was found and verified

            # Step 2: No DOI found, try title search with fuzzy matching
            title = citation.get("title", "")
            authors = citation.get("authors", [])
            year = citation.get("published", [None])[0]
            
            result = self._search_crossref_by_title(raw_ref, title, authors, year)
            match_found = False
            
            if result and result.get("title"):
                # Robust fuzzy matching like in the working script
                def normalize(text):
                    import string
                    return ''.join([c for c in text.lower() if c not in string.punctuation]).strip()
                
                ref_norm = normalize(raw_ref)
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
                    
                    # Update citation with verified data
                    citation["doi"] = result.get("doi")
                    citation["verified"] = True
                    if result.get("title") and not citation.get("title"):
                        citation["title"] = result["title"]
                    if result.get("authors") and not citation.get("authors"):
                        citation["authors"] = result["authors"]
                    if result.get("published") and not citation.get("published"):
                        citation["published"] = result["published"]
                    
                    verified_citations.append(citation)
                    seen_titles.add(title_norm)
                    match_found = True
            
            if not match_found:
                # Keep the citation but mark as unverified
                citation["verified"] = False
                verified_citations.append(citation)

        return verified_citations

    def _get_references_section(self, text: str) -> str:
        """
        Extracts the text after the 'References' heading (case-insensitive).
        """
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

    def _search_crossref_by_title(self, raw_ref: str, title: str, authors: list, year: int):
        """Improved: search CrossRef by title with fuzzy + author matching."""
        url = "https://api.crossref.org/works"

        def normalize(text):
            return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', text.lower())).strip()

        try:
            # Use both the raw reference and the extracted title for better results
            query = raw_ref if len(raw_ref) > len(title) else title
            response = requests.get(url, params={"query.title": query, "rows": 5}, timeout=5)
            if response.status_code != 200:
                return None

            items = response.json().get("message", {}).get("items", [])
            if not items:
                return None

            ref_norm = normalize(raw_ref)
            best_item, best_score = None, 0

            for item in items:
                item_title = item.get("title", [""])[0]
                title_norm = normalize(item_title)

                score = max(
                    fuzz.ratio(ref_norm, title_norm),
                    fuzz.partial_ratio(ref_norm, title_norm),
                    fuzz.token_set_ratio(ref_norm, title_norm)
                )

                # Small boost if any author's surname appears in ref
                if "author" in item:
                    item_authors = [a.get("family", "").lower() for a in item.get("author", [])]
                    if any(a and a in ref_norm for a in item_authors):
                        score += 5

                # Small boost if year matches
                item_year = None
                if "published-print" in item and "date-parts" in item["published-print"]:
                    item_year = item["published-print"]["date-parts"][0][0]
                elif "issued" in item and "date-parts" in item["issued"]:
                    item_year = item["issued"]["date-parts"][0][0]
                
                if year and item_year and year == item_year:
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

        return None

    # Keep the old methods for backward compatibility if needed
    def extract_dois(self, text: str):
        """Alias for backward compatibility"""
        return self._extract_dois(text)

    def extract_references(self, text: str):
        """Alias for backward compatibility"""
        return self._extract_references(text)

    def verify_doi_crossref(self, doi: str):
        """Alias for backward compatibility"""
        return self._verify_doi_crossref(doi)

    def search_crossref_by_title(self, title: str):
        """Simplified version for backward compatibility"""
        return self._search_crossref_by_title(title, title, [], None)


multi_analysis_service = Multi_AnalysisService()