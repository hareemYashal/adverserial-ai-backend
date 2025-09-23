# app/routes/analyze_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import asyncio
import logging

from app.database import get_db
from app.services.multi_analysis_service import multi_analysis_service
from app.models.document import Document
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/multi_analyze", tags=["Analysis"])

@router.post("/")
async def multi_analyze_document(
    project_id: int,
    document_id: int,
    persona_names: List[str],  # Now accepts multiple personas
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    logger.info(f" [START] Multi-analysis for {len(persona_names)} personas: {persona_names}")
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.content:
        raise HTTPException(status_code=400, detail="Document has no extracted content")

    try:
        # Extract and verify citations ONCE for all personas
        logger.info(" [STEP 1] Extracting references section...")
        references_text = multi_analysis_service._get_references_section(document.content)
        
        logger.info(" [STEP 2] Extracting citations...")
        citations_result = await multi_analysis_service.extract_citations_llm_async(references_text)
        citations = citations_result.get("citations", []) if citations_result else []
        
        logger.info(" [STEP 3] Verifying citations and generating Google Scholar links...")
        verified_citations = await multi_analysis_service.verify_citations_llm_async(citations, document.content)

        # Run persona analysis in parallel with shared citations
        logger.info(f" [STEP 4] Running {len(persona_names)} persona analyses in parallel...")
        
        async def analyze_with_new_session(content, persona_name, verified_citations):
            # Create new DB session for each task
            from app.database import SessionLocal
            new_db = SessionLocal()
            try:
                return await multi_analysis_service.analyze(content, persona_name, new_db, verified_citations)
            finally:
                new_db.close()
        
        tasks = [
            analyze_with_new_session(document.content, persona_name, verified_citations)
            for persona_name in persona_names
        ]
        feedbacks = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for persona_name, result in zip(persona_names, feedbacks):
            if isinstance(result, Exception):
                logger.error(f"❌ [ERROR] {persona_name} analysis failed: {str(result)}")
                results.append({
                    "persona": persona_name,
                    "error": str(result)
                })
            else:
                results.append(result)

        logger.info(f" [COMPLETE] Multi-analysis finished. Total API calls: 5 (1 extraction + 1 additional + 3 personas)")
        return {
            "document_id": document_id,
            "project_id": project_id,
            "results": results
        }

    except Exception as e:
        logger.error(f" [FATAL ERROR] Multi-analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))