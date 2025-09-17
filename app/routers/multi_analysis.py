# app/routes/analyze_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import asyncio

from app.database import get_db
from app.services.multi_analysis_service import multi_analysis_service
from app.models.document import Document
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/multi_analyze", tags=["Analysis"])

@router.post("/")
async def multi_analyze_document(
    project_id: int,
    document_id: int,
    persona_names: List[str],  # Now accepts multiple personas
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.content:
        raise HTTPException(status_code=400, detail="Document has no extracted content")

    try:
        tasks = [
            multi_analysis_service.analyze(document.content, persona_name)

            for persona_name in persona_names
        ]
        feedbacks = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for persona_name, result in zip(persona_names, feedbacks):
            if isinstance(result, Exception):
                results.append({
                    "persona": persona_name,
                    "error": str(result)
                })
            else:
                results.append(result)
        # Use the improved verification flow: PubMed, OpenAlex, then Google Scholar
        citations_result = multi_analysis_service.extract_citations_llm(document.content)
        citations = citations_result.get("citations", []) if citations_result else []
        verified_citations = multi_analysis_service.verify_citations_llm(citations, document.content)


        return {
            "document_id": document_id,
            "project_id": project_id,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))