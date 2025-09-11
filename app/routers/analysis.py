from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analysis_service import analysis_service
from app.models.document import Document
from app.services.auth_service import get_current_user  # assuming you have JWT auth
from app.schemas.citation import CitationsResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])

class ExtractRequest(BaseModel):
    document_id: Optional[int] = None
    text: Optional[str] = None

@router.post("/")
def analyze_document(
    project_id: int,
    document_id: int,
    persona_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.content:
        raise HTTPException(status_code=400, detail="Document has no extracted content")

    try:
        feedback = analysis_service.analyze(document.content, persona_name)
        return {"persona": persona_name, "feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-references", response_model=CitationsResponse)
def extract_references(
    req: ExtractRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not req.document_id and not req.text:
        raise HTTPException(status_code=400, detail="Provide document_id or text")

    raw_text = ""
    if req.document_id:
        doc = db.query(Document).filter(Document.id == req.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        raw_text = doc.content  # adapt field name if needed
    else:
        raw_text = req.text

    try:
        out = analysis_service.extract_citations_llm(raw_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(exc)}")
    return out
