# app/services/multi_analysis_service.py
import os
import re
import json
import requests
from openai import AsyncOpenAI
from openai import OpenAI
from app.services.persona_services import persona_service
from app.config import OPENAI_API_KEY
from urllib.parse import quote_plus

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

    def get_google_scholar_links_llm(self, citations: list) -> list:
        """
        Use OpenAI to extract Google Scholar links for a list of citation strings.
        Returns a list of dicts in the required JSON format.
        """
        if not citations:
            return []

        prompt = (
            "You are a scholarly assistant. For each citation below, search Google Scholar and return the best direct Google Scholar result link for that work. "
            "If no exact match is found, return the most relevant Google Scholar search link for the citation.\n\n"
            "Return ONLY a valid JSON array of objects, each with these fields:\n"
            "- 'title': the title of the work,\n"
            "- 'authors': a list of author names (if available, else an empty list),\n"
            "- 'published': a list with the publication year as an integer (if available, else an empty list),\n"
            "- 'doi': the best Google Scholar result link (or search link if no direct result),\n"
            "- 'valid': true if a link is found, false otherwise,\n"
            "- 'additional_citation': false\n\n"
            "CITATIONS:\n"
        )
        for idx, c in enumerate(citations, 1):
            prompt += f"{idx}. {c}\n"
        prompt += "\nReturn ONLY the JSON array, no extra text, no markdown."

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a scholarly assistant that returns only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=2000,
            )
            text_out = response.choices[0].message.content.strip()
            return self.safe_parse_json(text_out)
        except Exception as e:
            print(f"[Google Scholar LLM Extraction Error] {e}")
            return []

    def _get_google_scholar_link(self, title: str):
        """Generate a Google Scholar search link for the given title."""
        return f"https://scholar.google.com/scholar?q={quote_plus(title)}"

    def verify_citations_llm(self, references: list, paper_content: str = None) -> list:
        """
        Validate references via PubMed/OpenAlex/Google Scholar API.
        Returns a list of citation dicts with required fields.
        """
        verified_refs = []

        # First verify all existing references
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

            # Try PubMed first, then OpenAlex, then Google Scholar
            verified_ref = self._verify_reference_with_pubmed(title, authors, year)
            if not verified_ref["valid"]:
                verified_ref = self._verify_reference_with_openalex(title, authors, year)
                # Enforce valid: False if doi is None
                if verified_ref["doi"] is None:
                    verified_ref["valid"] = False
            if not verified_ref["valid"]:
                gs_link = self._get_google_scholar_link(title)
                verified_ref = {
                    "title": title,
                    "authors": authors,
                    "published": [year] if year else [],
                    "doi": gs_link if gs_link else None,
                    "valid": True if gs_link else False,
                    "additional_citation": False
                }

            verified_refs.append(verified_ref)

        # Get additional citations (if requested) and add them at the end
        if paper_content:
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

    def _get_additional_citations(self, paper_content: str) -> list:
        """Get additional relevant citations based on paper content"""
        prompt = (
            "Based on the following paper content, suggest 6-7 highly relevant academic references that are NOT already present in the references section of the document. "
            "Do NOT suggest any citation that is already listed in the references. "
            "Return ONLY a JSON array of objects with fields: title, authors, published.\n\n"
            f"Paper Content Excerpt:\n{paper_content[:2000]}\n\n"
            "Example format:\n"
            "[\n"
            '  {"title": "Example Title", "authors": ["Author1, A.", "Author2, B."], "published": [2020]}\n'
            "]"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a scholarly assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )
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
                # Verify the suggested citation: PubMed first, then OpenAlex, then Google Scholar
                verified = self._verify_reference_with_pubmed(title, authors, year)
                if not verified["valid"]:
                    verified = self._verify_reference_with_openalex(title, authors, year)
                if not verified["valid"]:
                    gs_link = self._get_google_scholar_link(title)
                    verified = {
                        "title": title,
                        "authors": authors,
                        "published": [year] if year else [],
                        "doi": gs_link if gs_link else None,
                        "valid": True if gs_link else False,
                        "additional_citation": False
                    }
                # Enforce valid: False if doi is None
                if verified["doi"] is None:
                    verified["valid"] = False
                verified_suggestions.append(verified)
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

    def _verify_reference_with_pubmed(self, title: str, authors: list, year: int):
        """Query PubMed to validate a reference with strict matching"""
        if not title:
            return self._create_fallback_ref(title, authors, year)
            
        # First search for the article
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": f'"{title}"[Title]',
            "retmode": "json",
            "retmax": 3
        }
        
        if year:
            search_params["term"] += f" AND {year}[Date - Publication]"
        
        try:
            search_response = requests.get(search_url, params=search_params, timeout=20)
            if search_response.status_code == 200:
                search_data = search_response.json()
                id_list = search_data.get("esearchresult", {}).get("idlist", [])
                
                if not id_list:
                    return self._create_fallback_ref(title, authors, year)
                
                # Get details for the first result
                summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                summary_params = {
                    "db": "pubmed",
                    "id": id_list[0],
                    "retmode": "json"
                }
                
                summary_response = requests.get(summary_url, params=summary_params, timeout=10)
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    result = summary_data.get("result", {}).get(id_list[0], {})
                    
                    pub_title = result.get("title", "")
                    pub_date = result.get("pubdate", "")
                    
                    # Extract year from publication date
                    pub_year = None
                    if pub_date:
                        year_match = re.search(r'(\d{4})', pub_date)
                        if year_match:
                            pub_year = year_match.group(1)
                    
                    # Strict matching
                    if year and pub_year and int(pub_year) != int(year):
                        return self._create_fallback_ref(title, authors, year)
                    
                    if not self._is_exact_title_match(title, pub_title):
                        return self._create_fallback_ref(title, authors, year)
                    
                    # Extract authors
                    pub_authors = []
                    for author in result.get("authors", []):
                        if author.get("name"):
                            pub_authors.append(author.get("name"))
                        elif author.get("lastname") and author.get("forename"):
                            pub_authors.append(f"{author.get('lastname')}, {author.get('forename')}")
                    
                    # Get DOI from article IDs
                    doi = None
                    for article_id in result.get("articleids", []):
                        if article_id.get("idtype") == "doi":
                            doi = article_id.get("value")
                            break
                    
                    return {
                        "title": pub_title,
                        "authors": pub_authors,
                        "published": [int(pub_year)] if pub_year and pub_year.isdigit() else [],
                        "doi": f"https://doi.org/{doi}" if doi else None,
                        "valid": True,
                        "additional_citation": False
                    }
                    
        except Exception as e:
            print(f"[PubMed Error] {e}")

        return self._create_fallback_ref(title, authors, year)

    def _verify_reference_with_openalex(self, title: str, authors: list, year: int):
        """Query OpenAlex to validate a reference with strict matching"""
        if not title:
            return self._create_fallback_ref(title, authors, year)

        url = "https://api.openalex.org/works"
        params = {
            "filter": f"title.search:{title}",
            "per-page": 5
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                results = response.json().get("results", [])
                for item in results:
                    pub_year = item.get("publication_year")
                    if year and pub_year and int(pub_year) != int(year):
                        continue
                    item_title = item.get("title", "")
                    if not self._is_exact_title_match(title, item_title):
                        continue
                    item_authors = []
                    for a in item.get("authorships", []):
                        author_name = a.get("author", {}).get("display_name")
                        if author_name:
                            item_authors.append(author_name)
                    if authors and not self._are_authors_similar(authors, item_authors):
                        continue
                    doi = item.get("doi")
                    return {
                        "title": item_title,
                        "authors": item_authors,
                        "published": [pub_year] if pub_year else [],
                        "doi": doi if doi else None,
                        "valid": True,
                        "additional_citation": False
                    }
        except Exception as e:
            print(f"[OpenAlex Error] {e}")

        return self._create_fallback_ref(title, authors, year)

    def _create_fallback_ref(self, title: str, authors: list, year: int):
        """Create a fallback reference when verification fails"""
        return {
            "title": title,
            "authors": authors,
            "published": [year] if year else [],
            "doi": None,
            "valid": False,
            "additional_citation": False
        }

    def _is_exact_title_match(self, title1: str, title2: str) -> bool:
        """Check if two titles match exactly (case-insensitive, punctuation ignored)"""
        if not title1 or not title2:
            return False
            
        # Normalize titles: lowercase, remove punctuation, extra spaces
        normalize = lambda t: re.sub(r'[^\w\s]', '', t.lower()).strip()
        t1 = normalize(title1)
        t2 = normalize(title2)
        
        return t1 == t2

    def _are_authors_similar(self, authors1: list, authors2: list) -> bool:
        """Check if author lists are similar"""
        if not authors1 or not authors2:
            return True
            
        # Extract last names
        def extract_last_names(authors):
            last_names = []
            for author in authors:
                if isinstance(author, str):
                    if ',' in author:
                        last_names.append(author.split(',')[0].strip().lower())
                    else:
                        parts = author.split()
                        if parts:
                            last_names.append(parts[-1].lower())
            return last_names
        
        last_names1 = extract_last_names(authors1)
        last_names2 = extract_last_names(authors2)
        
        # If we can't extract names, assume they match
        if not last_names1 or not last_names2:
            return True
            
        # Check if at least one author matches
        return any(name in last_names2 for name in last_names1)

    async def analyze(self, document_text: str, persona_name: str, db=None) -> dict:
        # Use persona_service to support both static and dynamic personas
        persona = persona_service.get_by_name(persona_name, db)
        if not persona:
            raise ValueError(f"Persona '{persona_name}' not found")

        system_prompt = persona["system_prompt"]

        # Persona-based LLM analysis
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
        
        # Verify citations
        verified_citations = self.verify_citations_llm(
            citations_json.get("citations", []), 
            document_text
        )

        return {
            "persona": persona_name,
            "feedback": {
                "analysis": llm_output,
                "citations": verified_citations  # Only one citations array
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
        prompt = PROMPT.replace("<<<REFERENCES_TEXT>>>", references_text[:150000])
        try:
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
        except Exception as e:
            print(f"[Citation Extraction Error] {e}")
            return {"citations": []}

    def _get_references_section(self, text: str) -> str:
        match = re.search(r'(?i)\bReferences\b', text)
        if match:
            return text[match.end():].strip()
        return text

# Singleton
multi_analysis_service = Multi_AnalysisService()