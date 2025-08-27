from pydantic import BaseModel, Field
from typing import List, Optional

class IngestResponse(BaseModel):
    files_ingested: int
    chunks_added: int
    collection: str

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: Optional[int] = None
    session_id: Optional[str] = None

class SourceChunk(BaseModel):
    id: str
    text: str
    metadata: dict
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    used_llm: bool
    session_id: Optional[str] = None

class CreateSessionResponse(BaseModel):
    session_id: str