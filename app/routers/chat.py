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
from app.services.auth_service import get_current_user
from app.models.user import User
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    docs, metadatas, distances, chunk_ids = [], [], [], []

    # Process multiple files if uploaded
    if files and len(files) > 0 and any(f.filename for f in files):
        for file in files:
            if not file.filename or file.filename == '':  # Skip empty uploads
                continue
            
            # Check if document already exists in this project (by filename and size)
            file_size_temp = len(await file.read())
            await file.seek(0)  # Reset file pointer
            
            existing_doc = db.query(Document).filter(
                Document.filename == file.filename,
                Document.project_id == project_id,
                Document.file_size == file_size_temp
            ).first()
            
            if existing_doc:
                # Use existing document
                doc_ids.append(existing_doc.id)
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

            # 4. Create Document record in DB (only if not exists)
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

        # 6. Get context using vector search
        try:
            docs, metadatas, distances, chunk_ids = similarity_search(
               query=question,
               top_k=15,  # More chunks for multiple files
               filters={"session_id": sid}
            )
            context = "\n\n".join(docs)
            print(f"Using vector search from session {sid}: {len(context)} characters")
        except Exception as e:
            print(f"Vector search failed: {e}")
            context = ""
    
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
        
        # Use vector search for document_ids
        try:
            # First, ensure documents are chunked and in vector DB
            all_docs = db.query(Document).filter(Document.id.in_(doc_id_list)).all()
            for doc in all_docs:
                if doc.content:
                    # Check if already chunked by looking for existing chunks
                    existing_docs, _, _, _ = similarity_search(query="test", top_k=1, filters={"document_id": doc.id})
                    if not existing_docs:  # No chunks found, need to chunk
                        print(f"⚡ Document {doc.id} not chunked, adding chunks...")
                        chunks = chunk_text(doc.content, max_tokens=150, overlap_sentences=2)
                        ids = [str(uuid.uuid4()) for _ in chunks]
                        metas = [{"document_id": doc.id, "session_id": sid} for _ in chunks]
                        add_chunks(chunks, metas, ids)
                    else:
                        print(f"⚡ Document {doc.id} already chunked, skipping")
            
            # Now do vector search across all requested documents
            if len(doc_id_list) == 1:
                # Single document filter - increase chunks for author questions
                author_keywords = ['author', 'written by', 'by ', 'wrote']
                is_author_question = any(keyword in question.lower() for keyword in author_keywords)
                top_k = 35 if is_author_question else 25
                
                docs, metadatas, distances, chunk_ids = similarity_search(
                    query=question,
                    top_k=top_k,
                    filters={"document_id": doc_id_list[0]}  # Single document ID
                )
            else:
                # Multiple documents - search each document separately and combine
                # Dynamic chunks per document based on total count
                chunks_per_doc = max(8, min(20, 80 // len(doc_id_list)))  # 8-20 chunks per doc
                print(f"📊 Using {chunks_per_doc} chunks per document for {len(doc_id_list)} documents")
                
                all_docs, all_metas, all_dists, all_ids = [], [], [], []
                for doc_id in doc_id_list:
                    doc_docs, doc_metas, doc_dists, doc_ids_list = similarity_search(
                        query=question,
                        top_k=chunks_per_doc,
                        filters={"document_id": doc_id}
                    )
                    all_docs.extend(doc_docs)
                    all_metas.extend(doc_metas)
                    all_dists.extend(doc_dists)
                    all_ids.extend(doc_ids_list)
                
                # Sort by distance and take top 30 for maximum coverage
                combined = list(zip(all_docs, all_metas, all_dists, all_ids))
                combined.sort(key=lambda x: x[2])  # Sort by distance
                docs, metadatas, distances, chunk_ids = zip(*combined[:30]) if combined else ([], [], [], [])
                docs, metadatas, distances, chunk_ids = list(docs), list(metadatas), list(distances), list(chunk_ids)
            
            # Group chunks by document for better context formatting
            doc_chunks = {}
            for i, meta in enumerate(metadatas):
                doc_id = meta.get("document_id")
                if doc_id not in doc_chunks:
                    doc_chunks[doc_id] = []
                doc_chunks[doc_id].append(docs[i])
            
            # Format context with document separation
            context_parts = []
            for i, doc_id in enumerate(doc_chunks.keys(), 1):
                doc_content = "\n\n".join(doc_chunks[doc_id])
                context_parts.append(f"=== DOCUMENT {i} ===\n{doc_content}")
            
            context = "\n\n" + "\n\n".join(context_parts) + "\n\n"
            print(f"Using RAG vector search from {len(doc_id_list)} documents: {len(context)} characters")
            doc_ids = doc_id_list
        except Exception as e:
            print(f"Vector search failed: {e}")
            context = ""
            doc_ids = doc_id_list
    
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
            prompt = persona_prompt or f"You are {persona} - an ADVERSARIAL CRITIC whose job is to challenge and test arguments. You are the user's intellectual opponent, not their supporter. ADVERSARIAL MODE: 1. Challenge the document's arguments systematically. 2. Be critically rigorous - identify flaws and weaknesses. 3. Quote exact text when making critiques. 4. Attack logical fallacies and poor reasoning directly. 5. Your goal: Test arguments through adversarial analysis, not validate them."
            
            new_persona = Persona(
                name=persona,
                description=description,
                personality_traits=traits,
                system_prompt=prompt,
                user_id=current_user.id,  # Associate with current user
                is_default=False
            )
            db.add(new_persona)
            db.commit()
            db.refresh(new_persona)
        # Optionally, remove the usage key to avoid repeated inserts
        del persona_usage[usage_key]

    # Build system prompt - try to load from database first
    if persona_prompt:
        system_prompt = persona_prompt
    else:
        # Try to load persona from database
        db_persona = db.query(Persona).filter(func.lower(Persona.name) == persona.lower()).first()
        if db_persona and db_persona.system_prompt:
            system_prompt = db_persona.system_prompt
        else:
            # Fallback to adversarial prompt
            system_prompt = (
                f"You are {persona} - an ADVERSARIAL CRITIC whose job is to challenge arguments. "
                f"You are the user's intellectual opponent, not their supporter. "
                f"ADVERSARIAL MODE:\n"
                f"1. Challenge the document's arguments systematically.\n"
                f"2. Be critically rigorous - identify flaws and weaknesses.\n"
                f"3. Quote exact text when making critiques.\n"
                f"4. Attack logical fallacies and poor reasoning directly. do not say something like Document id : 25 . 34 , 34 use proper title of the document\n"
                f"5. Your goal: Test arguments through adversarial analysis, not validate them.\n"
                f"6. Do NOT say something like 'Adversarial Critique:' - integrate critique naturally into your response."
            )

    history = get_history(sid)

    try:
        # Call the LLM with persona prompt and (optionally) document context
        # Handle different contexts
        if not context:
            final_context = f"No document provided. As {persona}, provide a critical adversarial analysis of the question asked. Challenge assumptions, identify potential flaws in reasoning, and offer rigorous intellectual critique from your philosophical perspective."
        else:
            final_context = f"Document content:\n{context}\n\nAs {persona}, first ANSWER THE USER'S QUESTION directly, then provide adversarial critique if relevant. Be helpful and informative while maintaining your critical perspective. Do NOT say something like 'Adversarial Critique:' - integrate critique naturally."
            
        answer = synthesize_answer_openai(
            question=question,
            context=final_context,
            history=history,
            system_prompt=system_prompt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")
    
    # Ensure we have a valid answer
    if not answer or answer.strip() == "":
        answer = f"I am {persona} and I'm ready to help you. Please ask me a question and I'll respond from my philosophical perspective."

    append_history(sid, "user", question)
    append_history(sid, "assistant", answer or "No answer available.")

    response = {
        "answer": answer,
        "session_id": sid,
        "persona": persona,
        "used_llm": bool(answer),
        "files_processed": len(doc_ids)
    }
    if doc_ids:
        response["document_ids"] = doc_ids
        if docs:  # Only add sources if vector search was used
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

