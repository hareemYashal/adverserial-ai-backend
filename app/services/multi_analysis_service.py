# app/services/multi_analysis_service.py
import os
import re
import json
import requests
import logging
from openai import AsyncOpenAI
from openai import OpenAI
from app.services.persona_services import persona_service
from app.config import OPENAI_API_KEY
from urllib.parse import quote_plus

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Multi_AnalysisService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY)
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
    
    def _normalize_title(self, title: str) -> str:
        """Normalize a title for deduplication: lowercase, remove punctuation and extra spaces."""
        if not title:
            return ""
        return re.sub(r'[^\w\s]', '', title.lower()).strip()

    def _get_google_scholar_link_enhanced(self, title: str, authors: list = None, year: int = None):
        """Generate enhanced Google Scholar search link with title, author, and year."""
        query_parts = [title]
        
        if authors and len(authors) > 0:
            # Use first author's last name
            first_author = authors[0]
            if ',' in first_author:
                author_lastname = first_author.split(',')[0].strip()
            else:
                author_parts = first_author.split()
                author_lastname = author_parts[-1] if author_parts else first_author
            query_parts.append(author_lastname)
        
        if year:
            query_parts.append(str(year))
        
        query = ' '.join(query_parts)
        return f"https://scholar.google.com/scholar?q={quote_plus(query)}"

    async def verify_citations_llm_async(self, references: list, paper_content: str = None) -> list:
        """Async version of citation verification"""
        logger.info(f"🔗 [CITATIONS] Processing {len(references)} citations - NO API calls")
        verified_refs = []

        # Process all existing references
        for ref in references:
            if isinstance(ref, dict):  # structured ref
                title = ref.get("title", "").strip()
                authors = ref.get("authors", [])
                year = None
                if isinstance(ref.get("published"), list) and ref["published"]:
                    year = ref["published"][0]
                elif isinstance(ref.get("published"), int):
                    year = ref.get("published")
            else:  # fallback if ref is a string
                title = str(ref).strip()
                authors = []
                year = None

            if not title:
                continue

            # Generate Google Scholar link (no API call)
            gs_link = self._get_google_scholar_link_enhanced(title, authors, year)
            verified_ref = {
                "title": title,
                "authors": authors,
                "published": [year] if year else [],
                "doi": gs_link,
                "valid": True,
                "additional_citation": False
            }

            verified_refs.append(verified_ref)

        # Get additional citations (if requested) and add them at the end
        if paper_content:
            logger.info("📚 [ADDITIONAL] Getting additional citations...")
            additional_citations = await self._get_additional_citations_async(paper_content)
            # Build set of normalized titles from main citations
            main_titles = set(self._normalize_title(ref["title"]) for ref in verified_refs if ref.get("title"))
            seen_additional = set()
            for citation in additional_citations:
                norm_title = self._normalize_title(citation.get("title", ""))
                # Skip if already in main citations or already added as additional
                if not norm_title or norm_title in main_titles or norm_title in seen_additional:
                    continue
                citation["additional_citation"] = True
                verified_refs.append(citation)
                seen_additional.add(norm_title)

        return verified_refs

    def verify_citations_llm(self, references: list, paper_content: str = None) -> list:
        """
        Process citations and generate Google Scholar links - NO API calls.
        """
        logger.info(f"🔗 [CITATIONS] Processing {len(references)} citations - NO API calls")
        verified_refs = []

        # Process all existing references
        for ref in references:
            if isinstance(ref, dict):  # structured ref
                title = ref.get("title", "").strip()
                authors = ref.get("authors", [])
                year = None
                if isinstance(ref.get("published"), list) and ref["published"]:
                    year = ref["published"][0]
                elif isinstance(ref.get("published"), int):
                    year = ref.get("published")
            else:  # fallback if ref is a string
                title = str(ref).strip()
                authors = []
                year = None

            if not title:
                continue

            # Generate Google Scholar link (no API call)
            gs_link = self._get_google_scholar_link_enhanced(title, authors, year)
            verified_ref = {
                "title": title,
                "authors": authors,
                "published": [year] if year else [],
                "doi": gs_link,
                "valid": True,
                "additional_citation": False
            }

            verified_refs.append(verified_ref)

        # Get additional citations (if requested) and add them at the end
        if paper_content:
            logger.info("📚 [ADDITIONAL] Getting additional citations...")
            additional_citations = self._get_additional_citations(paper_content)
            # Build set of normalized titles from main citations
            main_titles = set(self._normalize_title(ref["title"]) for ref in verified_refs if ref.get("title"))
            seen_additional = set()
            for citation in additional_citations:
                norm_title = self._normalize_title(citation.get("title", ""))
                # Skip if already in main citations or already added as additional
                if not norm_title or norm_title in main_titles or norm_title in seen_additional:
                    continue
                citation["additional_citation"] = True
                verified_refs.append(citation)
                seen_additional.add(norm_title)

        return verified_refs

    async def _get_additional_citations_async(self, paper_content: str) -> list:
        """Async version of getting additional citations"""
        prompt = (
            "You are a precise academic librarian with access to Google Scholar database. Based on the paper content below, suggest 6-7 REAL academic references that definitely exist on Google Scholar.\n\n"
            "ABSOLUTE REQUIREMENTS:\n"
            "1. ONLY suggest papers that you are 100% certain exist on Google Scholar\n"
            "2. Use EXACT titles as they appear in the actual publications - no modifications\n"
            "3. Use EXACT author names as they appear in Google Scholar\n"
            "4. Use EXACT publication years from the actual papers\n"
            "5. Focus on highly-cited, well-known papers in the field\n"
            "6. If you are not 100% sure about a title/author/year combination, DO NOT include it\n\n"
            f"Paper Content:\n{paper_content[:2000]}\n\n"
            "EXAMPLES of papers that definitely exist:\n"
            "- Health Economics: 'Methods for the Economic Evaluation of Health Care Programmes' by Drummond et al.\n"
            "- Medical Ethics: 'Principles of Biomedical Ethics' by Beauchamp & Childress\n"
            "- Philosophy: 'A Theory of Justice' by John Rawls\n\n"
            "Return ONLY a JSON array with EXACT information:\n"
            "[\n"
            '  {"title": "EXACT Title as Published", "authors": ["Exact, A.B.", "Name, C.D."], "published": [EXACT_YEAR]}\n'
            "]\n\n"
            "WARNING: If you suggest a fake citation, it will be detected. Only suggest papers you are absolutely certain exist."
        )

        try:
            logger.info("🤖 [API CALL 2/5] OpenAI - Getting additional citations")
            response = await self.async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise academic librarian. Return only valid JSON with REAL citations."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=600,
            )
            logger.info("✅ [API CALL 2/5] Additional citations - SUCCESS")
            text_out = response.choices[0].message.content.strip()
            
            suggested = self.safe_parse_json(text_out)
            verified_suggestions = []
            for sug in suggested:
                title = sug.get("title", "").strip()
                authors = sug.get("authors", [])
                year = None
                if isinstance(sug.get("published"), list) and sug["published"]:
                    year = sug["published"][0]
                if not title:
                    continue
                # Generate Google Scholar link (no API call)
                gs_link = self._get_google_scholar_link_enhanced(title, authors, year)
                verified = {
                    "title": title,
                    "authors": authors,
                    "published": [year] if year else [],
                    "doi": gs_link,
                    "valid": True,
                    "additional_citation": True
                }
                verified_suggestions.append(verified)
            logger.info(f"✅ [ADDITIONAL] Generated {len(verified_suggestions)} additional citations")
            return verified_suggestions
            
        except Exception as e:
            print(f"[Additional Citations Error] {e}")
            return []

    def _get_additional_citations(self, paper_content: str) -> list:
        """Get additional relevant citations based on paper content"""
        prompt = (
            "You are a precise academic librarian with access to Google Scholar database. Based on the paper content below, suggest 6-7 REAL academic references that definitely exist on Google Scholar.\n\n"
            "ABSOLUTE REQUIREMENTS:\n"
            "1. ONLY suggest papers that you are 100% certain exist on Google Scholar\n"
            "2. Use EXACT titles as they appear in the actual publications - no modifications\n"
            "3. Use EXACT author names as they appear in Google Scholar\n"
            "4. Use EXACT publication years from the actual papers\n"
            "5. Focus on highly-cited, well-known papers in the field\n"
            "6. If you are not 100% sure about a title/author/year combination, DO NOT include it\n\n"
            f"Paper Content:\n{paper_content[:2000]}\n\n"
            "EXAMPLES of papers that definitely exist:\n"
            "- Health Economics: 'Methods for the Economic Evaluation of Health Care Programmes' by Drummond et al.\n"
            "- Medical Ethics: 'Principles of Biomedical Ethics' by Beauchamp & Childress\n"
            "- Philosophy: 'A Theory of Justice' by John Rawls\n\n"
            "Return ONLY a JSON array with EXACT information:\n"
            "[\n"
            '  {"title": "EXACT Title as Published", "authors": ["Exact, A.B.", "Name, C.D."], "published": [EXACT_YEAR]}\n'
            "]\n\n"
            "WARNING: If you suggest a fake citation, it will be detected. Only suggest papers you are absolutely certain exist."
        )

        try:
            logger.info("🤖 [API CALL 2/5] OpenAI - Getting additional citations")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise academic librarian. Return only valid JSON with REAL citations."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=600,
            )
            logger.info("✅ [API CALL 2/5] Additional citations - SUCCESS")
            text_out = response.choices[0].message.content.strip()
            
            suggested = self.safe_parse_json(text_out)
            verified_suggestions = []
            for sug in suggested:
                title = sug.get("title", "").strip()
                authors = sug.get("authors", [])
                year = None
                if isinstance(sug.get("published"), list) and sug["published"]:
                    year = sug["published"][0]
                if not title:
                    continue
                # Generate Google Scholar link (no API call)
                gs_link = self._get_google_scholar_link_enhanced(title, authors, year)
                verified = {
                    "title": title,
                    "authors": authors,
                    "published": [year] if year else [],
                    "doi": gs_link,
                    "valid": True,
                    "additional_citation": True
                }
                verified_suggestions.append(verified)
            logger.info(f"✅ [ADDITIONAL] Generated {len(verified_suggestions)} additional citations")
            return verified_suggestions
            
        except Exception as e:
            print(f"[Additional Citations Error] {e}")
            return []

    def safe_parse_json(self, maybe_json: str):
        """Safely parse JSON from LLM output"""
        maybe_json = maybe_json.strip()
        maybe_json = re.sub(r"^```(?:json)?", "", maybe_json)
        maybe_json = re.sub(r"```$", "", maybe_json)
        maybe_json = maybe_json.strip()
        try:
            return json.loads(maybe_json)
        except Exception:
            # Try to find JSON array pattern
            m = re.search(r'(\[.*\])', maybe_json, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass
        return []

    async def analyze(self, document_text: str, persona_name: str, db=None, shared_citations=None) -> dict:
        # Use persona_service to support both static and dynamic personas
        persona = persona_service.get_by_name(persona_name, db)
        if not persona:
            raise ValueError(f"Persona '{persona_name}' not found")

        system_prompt = persona["system_prompt"]

        # Async persona-based LLM analysis
        logger.info(f"🎭 [API CALL] OpenAI - Analyzing with {persona_name} persona")
        response = await self.async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": document_text}
            ],
            temperature=0.7
        )
        llm_output = response.choices[0].message.content
        logger.info(f"✅ [API CALL] {persona_name} analysis - SUCCESS")

        return {
            "persona": persona_name,
            "feedback": {
                "analysis": llm_output,
                "citations": shared_citations if shared_citations else []
            }
        }

    def _get_references_section(self, text: str) -> str:
        # Try multiple reference section patterns
        patterns = [r'(?i)\bReferences\b', r'(?i)\bBibliography\b', r'(?i)\bWorks Cited\b', r'(?i)\bLiterature Cited\b']
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                refs_section = text[match.end():].strip()
                logger.info(f"📝 [DEBUG] Found References section: {len(refs_section)} characters")
                return refs_section
        
        # If no references section found, return last 30% of document
        split_point = int(len(text) * 0.7)
        refs_section = text[split_point:].strip()
        logger.info(f"⚠️ [DEBUG] No References section found, using last 30% of document: {len(refs_section)} characters")
        return refs_section

    async def extract_citations_llm_async(self, references_text: str) -> dict:
        """Async version of citation extraction."""
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
6. "valid" (boolean) — always false at extraction stage.

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
            "valid": false
        }
    ]
}

TEXT:
<<<REFERENCES_TEXT>>>
"""
        prompt = PROMPT.replace("<<<REFERENCES_TEXT>>>", references_text[:50000])
        logger.info(f"📝 [DEBUG] References text length: {len(references_text)} chars, using first 50000")
        try:
            logger.info("🤖 [API CALL 1/5] OpenAI - Extracting citations from document")
            response = await self.async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a JSON-only extractor for bibliographic references."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=4000,
            )
            logger.info("✅ [API CALL 1/5] Citation extraction - SUCCESS")
            text_out = response.choices[0].message.content.strip()
            
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
            citations_count = len(parsed.get("citations", []))
            logger.info(f"✅ [CITATIONS] Extracted {citations_count} citations from document")
            if citations_count <= 2:
                logger.info(f"⚠️ [DEBUG] Low citation count. LLM response: {text_out[:200]}...")
            return parsed
        except Exception as e:
            print(f"[Citation Extraction Error] {e}")
            return {"citations": []}

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
6. "valid" (boolean) — always false at extraction stage.

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
            "valid": false
        }
    ]
}

TEXT:
<<<REFERENCES_TEXT>>>
"""
        prompt = PROMPT.replace("<<<REFERENCES_TEXT>>>", references_text[:50000])
        logger.info(f"📝 [DEBUG] References text length: {len(references_text)} chars, using first 50000")
        try:
            logger.info("🤖 [API CALL 1/5] OpenAI - Extracting citations from document")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a JSON-only extractor for bibliographic references."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=4000,
            )
            logger.info("✅ [API CALL 1/5] Citation extraction - SUCCESS")
            text_out = response.choices[0].message.content.strip()
            
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
            citations_count = len(parsed.get("citations", []))
            logger.info(f"✅ [CITATIONS] Extracted {citations_count} citations from document")
            if citations_count <= 2:
                logger.info(f"⚠️ [DEBUG] Low citation count. LLM response: {text_out[:200]}...")
            return parsed
        except Exception as e:
            print(f"[Citation Extraction Error] {e}")
            return {"citations": []}

# Singleton
multi_analysis_service = Multi_AnalysisService()