from app.models.persona import Persona
from app.models import Document
from sqlalchemy import func

# Module-level dictionary to track persona usage per session
persona_usage = {}
from fastapi import APIRouter, Form, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.session import get_history, append_history
from app.services.llm import synthesize_answer_openai
from typing import List, Optional, Union, Any
import uuid

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

router = APIRouter(prefix="/api/persona-chat", tags=["Chat"])

@router.post("/simple")
async def chat_simple(
    project_id: int = Form(...),
    question: str = Form(...),
    persona: str = Form(...),
    persona_description: str = Form(None),
    persona_traits: str = Form(None),  # comma-separated traits
    persona_prompt: str = Form(None),
    session_id: str = Form(None),
    files: List[UploadFile] = Depends(parse_files),
    document_ids: str = Form(None),  # Comma-separated document IDs for follow-up questions
    db: Session = Depends(get_db)
):
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    import os
    import uuid
    from datetime import datetime
    from app.services.file_service import file_service
    from app.services.chunking import chunk_text
    from app.services.retrieval import add_chunks, similarity_search

    sid = session_id or str(uuid.uuid4())
    doc_ids = []
    context = ""

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

            # 3. Get file size
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

        # 6. Get context from ALL files in this session
        docs, metadatas, distances, chunk_ids = similarity_search(
           query=question,
           top_k=10,  # More chunks for multiple files
           filters={"session_id": sid}
        )
        context = "\n\n".join(docs)
    
    # If no files but document_ids provided (follow-up questions)
    elif document_ids:
        # Parse comma-separated document IDs
        try:
            doc_id_list = [int(x.strip()) for x in document_ids.split(',') if x.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document_ids format. Use comma-separated integers like: 60,61,62")
        
        if not doc_id_list:
            raise HTTPException(status_code=400, detail="No valid document IDs provided")
        
        # Get first document to extract session_id
        first_doc = db.query(Document).filter(Document.id == doc_id_list[0]).first()
        if not first_doc:
            raise HTTPException(status_code=404, detail=f"Document {doc_id_list[0]} not found")
        
        sid = session_id or first_doc.session_id
        
        # Get context from session (all documents in session)
        docs, metadatas, distances, chunk_ids = similarity_search(
           query=question,
           top_k=10,
           filters={"session_id": sid}
        )
        context = "\n\n".join(docs)
    
    # If neither files nor document_ids provided
    elif (not files or len(files) == 0) and not document_ids:
        sid = session_id or str(uuid.uuid4())
        context = ""  # No document context

    # Track persona usage per session
    usage_key = (sid, persona.lower())
    persona_usage[usage_key] = persona_usage.get(usage_key, 0) + 1

    # Save persona to DB after threshold (e.g., 3 uses in a session)
    USAGE_THRESHOLD = 1
    if persona_usage[usage_key] == USAGE_THRESHOLD:
        # Check if persona already exists (case-insensitive)
        existing = db.query(Persona).filter(func.lower(Persona.name) == persona.lower()).first()
        if not existing:
            # Use custom fields if provided
            description = persona_description or f"User-generated persona: {persona}"
            traits = persona_traits.split(',') if persona_traits else []
            prompt = persona_prompt or f"You are now impersonating {persona}. Adopt the communication style, personality traits, and reasoning approach of {persona}. Always stay in character and respond as if you are {persona}."
            
            new_persona = Persona(
                name=persona,
                description=description,
                personality_traits=traits,
                system_prompt=prompt
            )
            db.add(new_persona)
            db.commit()
            db.refresh(new_persona)
        # Optionally, remove the usage key to avoid repeated inserts
        del persona_usage[usage_key]

    # Build system prompt - use custom if provided, otherwise default
    if persona_prompt:
        system_prompt = persona_prompt
    else:
        system_prompt = (
            f"You are now impersonating {persona}. "
            f"Adopt the communication style, personality traits, and reasoning approach of {persona}. "
            f"Always stay in character and respond as if you are {persona}."
        )

    history = get_history(sid)

    try:
        # Call the LLM with persona prompt and (optionally) document context
        answer = synthesize_answer_openai(
            question=question,
            context=context,
            history=history,
            system_prompt=system_prompt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    append_history(sid, "user", question)
    append_history(sid, "assistant", answer or "No answer available.")

    response = {
        "answer": answer,
        "session_id": sid,
        "persona": persona,
        "used_llm": bool(answer),
        "files_processed": len(doc_ids)
    }
    if files and doc_ids:
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

