from app.models.persona import Persona
from sqlalchemy import func

# Module-level dictionary to track persona usage per session
persona_usage = {}
from fastapi import APIRouter, Form, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.session import get_history, append_history
from app.services.llm import synthesize_answer_openai
import uuid

router = APIRouter(prefix="/api/persona-chat", tags=["Chat"])

@router.post("/simple")
async def chat_simple(
    project_id: int = Form(...),
    question: str = Form(...),
    persona: str = Form(...),
    session_id: str = Form(None),
    file: UploadFile = File(None),
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
    doc_id = None
    context = ""

    # If a file is uploaded, process it for context
    if file:
        # 1. Save file to disk & metadata to DB
        file_meta = await file_service.save_file(file, project_id=project_id)
        file_path = file_meta["file_path"]
        file_type = file_meta["file_type"]
        unique_filename = file_meta["unique_filename"]

        # 2. Extract text
        try:
            text = file_service.extract_text(file_path=file_path, file_type=file_type)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Text extraction failed: {e}")

        # 3. Get file size from saved file on disk
        try:
            file_size = os.path.getsize(file_path)
        except Exception:
            file_size = 0

        # 4. Create Document record in DB
        from app.models import Document
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
        doc_id = document.id

        # 5. Chunk text and add to vector DB
        chunks = chunk_text(text, max_tokens=150, overlap_sentences=2)
        ids = [str(uuid.uuid4()) for _ in chunks]
        metas = [
            {
                "document_id": document.id,
                "persona": persona
            }
            for i in range(len(chunks))
        ]
        add_chunks(chunks, metas, ids)

        # 6. Retrieve similar docs for question context from chunks related to document
        docs, metadatas, distances, doc_ids = similarity_search(
           query=question,
           top_k=5,
           filters={"document_id": doc_id}
        )
        context = "\n\n".join(docs)

    # Track persona usage per session
    usage_key = (sid, persona.lower())
    persona_usage[usage_key] = persona_usage.get(usage_key, 0) + 1

    # Save persona to DB after threshold (e.g., 3 uses in a session)
    USAGE_THRESHOLD = 2
    if persona_usage[usage_key] == USAGE_THRESHOLD:
        # Check if persona already exists (case-insensitive)
        existing = db.query(Persona).filter(func.lower(Persona.name) == persona.lower()).first()
        if not existing:
            new_persona = Persona(
                name=persona,
                description=f"User-generated persona: {persona}",
                system_prompt=f"You are now impersonating {persona}. Adopt the communication style, personality traits, and reasoning approach of {persona}. Always stay in character and respond as if you are {persona}."
            )
            db.add(new_persona)
            db.commit()
            db.refresh(new_persona)
        # Optionally, remove the usage key to avoid repeated inserts
        del persona_usage[usage_key]

    # Dynamically build system prompt from persona
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
        "used_llm": bool(answer)
    }
    if file:
        response["document_id"] = doc_id
        response["sources"] = [
            {
                "id": doc_ids[i],
                "text": docs[i],
                "metadata": metadatas[i],
                "score": distances[i]
            }
            for i in range(len(docs))
        ]
    return response

