from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analysis_service import analysis_service
from app.models.document import Document
from app.services.auth_service import get_current_user  # assuming you have JWT auth

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])

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
