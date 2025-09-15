from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document
from app.services.file_service import file_service
from app.services.chunking import chunk_text
from app.services.retrieval import add_chunks, similarity_search
from app.services.session import get_history, append_history
from app.services.persona_services import persona_service

import uuid
import os
from datetime import datetime

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/")
async def chat_with_document(
    project_id: int = Form(...),
    question: str = Form(...),
    persona: str = Form(...),
    file: UploadFile = File(None),  # now optional
    document_id: int = Form(None),  # optional for follow-ups
    session_id: str = Form(None),  # optional for follow-ups
    db: Session = Depends(get_db)
):
    # If file uploaded => new document upload + process
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
        document = Document(
            filename=file.filename,
            unique_filename=unique_filename,
            content=text,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            project_id=project_id,
            session_id=session_id or str(uuid.uuid4()),
            is_processed=True,
            processed_at=datetime.utcnow()
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # 5. Chunk text and add to vector DB
        chunks = chunk_text(text, max_tokens=150, overlap_sentences=2)
        ids = [str(uuid.uuid4()) for _ in chunks]
        metas = [
            {
                "document_id": document.id,
                "persona":persona
            }
            for i in range(len(chunks))
        ]
        add_chunks(chunks, metas, ids)

        sid = document.session_id
        doc_id = document.id

    # If no file, use existing document_id and session_id
    else:
        if not document_id:
            raise HTTPException(status_code=400, detail="No file uploaded and no document_id provided")
        # Fetch document from DB
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        sid = session_id or document.session_id
        doc_id = document.id

    # 6. Get persona system prompt for LLM
    persona_obj = persona_service.get_by_name(persona, db)
    if not persona_obj:
        raise HTTPException(status_code=400, detail=f"Persona '{persona}' not found")

    system_prompt = persona_obj.get("system_prompt", "")

    # 7. Retrieve similar docs for question context from chunks related to document
    docs, metadatas, distances, doc_ids = similarity_search(
       query=question,
       top_k=5,
       filters={"document_id": doc_id}  # Filters by current doc only
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

    return {
        "answer": answer,
        "sources": [
            {
                "id": doc_ids[i],
                "text": docs[i],
                "metadata": metadatas[i],
                "score": distances[i]
            }
            for i in range(len(docs))
        ],
        "session_id": sid,
        "document_id": doc_id,
        "used_llm": bool(answer),
        "persona": persona_obj
    }
