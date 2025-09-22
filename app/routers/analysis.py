from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from app.database import get_db
from app.services.analysis_service import analysis_service
from app.models.document import Document
from app.services.auth_service import get_current_user  # assuming you have JWT auth
from app.schemas.citation import CitationsResponse
from app.schemas import CitationVerificationRequest, CitationVerificationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])

@router.post("/verify-citations", response_model=CitationVerificationResponse)
def verify_citations(
    req: CitationVerificationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Verify citations using LLM (CrossRef/PubMed logic) and suggest additional citations.
    """
    try:
        result = analysis_service.verify_citations_llm(req.references, req.paper_content)
        return CitationVerificationResponse(citations=result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Citation verification failed: {str(exc)}")


from pydantic import BaseModel
from typing import Optional

class ExtractRequest(BaseModel):
    document_id: Optional[int] = None
    text: Optional[str] = None
@router.post("/")
async def analyze_document(
    project_id: int,
    document_id: int,
    persona_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    logger.info(f" [START] Single analysis for persona: {persona_name}")
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.content:
        raise HTTPException(status_code=400, detail="Document has no extracted content")

    try:
        logger.info(" [STEP 1] Starting single persona analysis...")
        # This already includes verified citations in the feedback
        result = await analysis_service.analyze_async(document.content, persona_name)
        
        logger.info(f" [COMPLETE] Single analysis finished. Total API calls: 3 (1 extraction + 1 additional + 1 persona)")
        # Return the result directly - it already contains the properly structured citations
        return {
            "persona": persona_name,
            "feedback": result
        }
    except Exception as e:
        logger.error(f" [FATAL ERROR] Single analysis failed: {str(e)}")
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
