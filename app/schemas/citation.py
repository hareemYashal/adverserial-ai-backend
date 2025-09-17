from pydantic import BaseModel
from typing import List, Optional

class Citation(BaseModel):
    title: str
    authors: List[str]
    published: Optional[List[int]] = None
    doi: Optional[str] = None  # May contain DOI, PubMed, WorldCat, or Google Scholar link
    valid: bool = False

class CitationsResponse(BaseModel):
    citations: List[Citation]