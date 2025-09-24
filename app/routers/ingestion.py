from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document
from app.services.file_service import file_service
from app.services.chunking import chunk_text
from app.services.retrieval import add_chunks, similarity_search
from app.services.session import get_history, append_history
from app.services.persona_services import persona_service
from typing import List

import uuid
import os
from datetime import datetime

async def parse_files(request: Request) -> List[UploadFile]:
    """Custom function to handle files that can be empty strings from Swagger UI"""
    form = await request.form()
    files_data = form.getlist('files')
    
    valid_files = []
    for file_item in files_data:
        # Only add if it's actually an UploadFile with a filename
        if hasattr(file_item, 'filename') and file_item.filename:
            valid_files.append(file_item)
    
    return valid_files

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/")
async def chat_with_document(
    project_id: int = Form(...),
    question: str = Form(...),
    persona: str = Form(...),
    files: List[UploadFile] = Depends(parse_files),  # Handle empty files
    document_id: str = Form(None),  # Comma-separated document IDs
    session_id: str = Form(None),  # optional for follow-ups
    db: Session = Depends(get_db)
):
    sid = session_id or str(uuid.uuid4())
    doc_ids = []
    
    # Process multiple files if uploaded
    if files and len(files) > 0:
        for file in files:
            if not file.filename:  # Skip empty uploads
                continue
            
            # 1. Save file to disk & metadata to DB
            file_meta = await file_service.save_file(file, project_id=project_id)
            file_path = file_meta["file_path"]
            file_type = file_meta["file_type"]
            unique_filename = file_meta["unique_filename"]

            # 2. Extract text
            try:
                text = file_service.extract_text(file_path=file_path, file_type=file_type)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Text extraction failed for {file.filename}: {e}")

            # 3. Get file size from saved file on disk
            try:
                file_size = os.path.getsize(file_path)
            except Exception:
                file_size = 0

            # 4. Create Document record in DB
            document = Document(
                filename=file.filename,
                unique_filename=unique_filename,
                content=text,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                project_id=project_id,
                session_id=sid,
                is_processed=True,
                processed_at=datetime.utcnow()
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            doc_ids.append(document.id)

            # 5. Chunk text and add to vector DB
            chunks = chunk_text(text, max_tokens=150, overlap_sentences=2)
            ids = [str(uuid.uuid4()) for _ in chunks]
            metas = [
                {
                    "document_id": document.id,
                    "session_id": sid
                }
                for i in range(len(chunks))
            ]
            add_chunks(chunks, metas, ids)

    # If no files but document_id provided (follow-up questions)
    elif document_id:
        # Parse comma-separated document IDs
        try:
            doc_id_list = [int(x.strip()) for x in document_id.split(',') if x.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document_id format. Use comma-separated integers like: 60,61,62")
        
        if not doc_id_list:
            raise HTTPException(status_code=400, detail="No valid document IDs provided")
        
        # Get first document to extract session_id
        first_doc = db.query(Document).filter(Document.id == doc_id_list[0]).first()
        if not first_doc:
            raise HTTPException(status_code=404, detail=f"Document {doc_id_list[0]} not found")
        
        sid = session_id or first_doc.session_id
        doc_ids = doc_id_list
    
    # If neither files nor document_id provided
    elif (not files or len(files) == 0) and not document_id:
        sid = session_id or str(uuid.uuid4())
        doc_ids = []

    # 6. Get persona system prompt for LLM
    persona_obj = persona_service.get_by_name(persona, db)
    if not persona_obj:
        raise HTTPException(status_code=400, detail=f"Persona '{persona}' not found")

    system_prompt = persona_obj.get("system_prompt", "")

    # 7. Retrieve similar docs for question context from chunks related to session
    docs, metadatas, distances, chunk_ids = similarity_search(
       query=question,
       top_k=10,  # More chunks for multiple files
       filters={"session_id": sid}  # All docs in session
    )
    context = "\n\n".join(docs)

    # 8. Get chat history for session
    history = get_history(sid)

    # 9. Call LLM with custom system prompt instead of default
    from app.services.llm import synthesize_answer_openai

    answer = synthesize_answer_openai(
        question=question,
        context=context,
        history=history,
        system_prompt=system_prompt,
    )

    # 10. Save user Q & assistant A in history
    append_history(sid, "user", question)
    append_history(sid, "assistant", answer or "No answer available.")

    response = {
        "answer": answer,
        "session_id": sid,
        "persona": persona_obj,
        "used_llm": bool(answer),
        "files_processed": len(doc_ids)
    }
    
    if doc_ids:
        response["document_ids"] = doc_ids
        response["sources"] = [
            {
                "id": chunk_ids[i],
                "text": docs[i],
                "metadata": metadatas[i],
                "score": distances[i]
            }
            for i in range(len(docs))
        ]
    
    return response
