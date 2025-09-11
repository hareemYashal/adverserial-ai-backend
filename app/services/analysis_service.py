import os
import re
import json
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

        # Run normal analysis with persona
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": document_text}
            ],
            temperature=0.7
        )

        llm_output = response.choices[0].message.content

        # Extract references
        citations_json = self.extract_citations_llm(document_text)

        return {
            "persona": persona_name,
            "feedback": {
                "analysis": llm_output,
                "citations": citations_json["citations"]
            }
        }

    def extract_citations_llm(self, document_text: str) -> dict:
        """
        Extracts references section and parses citations into strict JSON.
        """
        references_text = self._get_references_section(document_text)

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
      "id": 1
    },
    {
      "title": "Advancement of learning and novum organum",
      "authors": ["Bacon, F."],
      "published": [1899],
      "id": 2
    }
  ]
}

TEXT:
<<<REFERENCES_TEXT>>>
"""

        # Insert references text into the prompt
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

        # --- Safe JSON parse ---
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

        def normalize_citation_object(c):
            out = {}
            out["title"] = c.get("title", "").strip()

            authors = c.get("authors", [])
            if isinstance(authors, str):
                # split multiple authors
                parts = re.split(r"\s+and\s+|;|, and |&", authors)
                authors = [p.strip() for p in parts if p.strip()]
            out["authors"] = authors

            if "published" in c and isinstance(c["published"], list) and c["published"]:
                out["published"] = c["published"]

            if "id" in c:
                out["id"] = c["id"]

            return out

        parsed = safe_parse_json(text_out)
        citations = parsed.get("citations", [])
        normalized = [normalize_citation_object(c) for c in citations]
        return {"citations": normalized}

    def _get_references_section(self, text: str) -> str:
        """
        Extracts the text after the 'References' heading (case-insensitive).
        """
        match = re.search(r'(?i)\bReferences\b', text)
        if match:
            return text[match.end():].strip()
        return text


# Singleton
analysis_service = AnalysisService()
