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
        verified_citations = []

        dois = multi_analysis_service.extract_dois(document.content)
        refs = multi_analysis_service.extract_references(document.content)
        # 1. Verify DOIs against CrossRef
        for doi in dois:
            result = multi_analysis_service.verify_doi_crossref(doi)
            if result:
                verified_citations.append(result)

        # 2. For non-DOI refs, try CrossRef title search
        for ref in refs:
            if any(doi in ref for doi in dois):
                continue  # already handled
            result = multi_analysis_service.search_crossref_by_title(ref)
            if result:
                verified_citations.append(result)
            else:
                # Keep raw if not found
                verified_citations.append({
                    "title": ref,
                    "source": "Unverified",
                    "valid": False
                })


        return {
            "document_id": document_id,
            "project_id": project_id,
            "results": results,
            "citations": verified_citations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
