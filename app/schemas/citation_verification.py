from typing import List, Optional
from pydantic import BaseModel

class CitationVerificationRequest(BaseModel):
    references: List[str]  # List of extracted references (could be DOIs, titles, etc.)
    paper_content: Optional[str] = None  # Full text or abstract of the uploaded paper

class CitationVerificationResponseItem(BaseModel):
    title: str
    authors: List[str]
    published: List[int]
    doi: Optional[str] = None  # May contain DOI, PubMed, WorldCat, or Google Scholar link
    valid: bool
    additional_citation: bool

class CitationVerificationResponse(BaseModel):
    citations: List[CitationVerificationResponseItem]
