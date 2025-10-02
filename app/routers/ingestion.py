from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document
from app.services.file_service import file_service
from app.services.chunking import chunk_text
from app.services.retrieval import add_chunks, similarity_search
from app.services.session import get_history, append_history
from app.services.persona_services import persona_service
from app.services.auth_service import get_current_user
from app.models.user import User
from sqlalchemy import func
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sid = session_id or str(uuid.uuid4())
    doc_ids = []
    
    # Process multiple files if uploaded
    if files and len(files) > 0:
        for file in files:
            if not file.filename:  # Skip empty uploads
                continue
            
            # Check if document already exists in this session
            existing_doc = db.query(Document).filter(
                Document.filename == file.filename,
                Document.session_id == sid,
                Document.project_id == project_id
            ).first()
            
            if existing_doc:
                print(f"Document {file.filename} already exists in session {sid}")
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
            chunks = chunk_text(text, max_tokens=350, overlap_sentences=2)
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

    # 6. Get persona system prompt for LLM - load from database first
    persona_obj = persona_service.get_by_name(persona, db)
    if not persona_obj:
        # Create fallback persona if not found
        persona_obj = {
            "name": persona,
            "system_prompt": f"You are {persona} - an ADVERSARIAL CRITIC whose job is to challenge and test arguments. You are the user's intellectual opponent, not their supporter."
        }

    system_prompt = persona_obj.get("system_prompt", "")
    # Add adversarial analysis instructions
    system_prompt += "\n\nADVERSARIAL MODE:\n" + \
                    "1. You are the user's intellectual opponent - challenge their arguments.\n" + \
                    "2. Systematically test the document's claims and reasoning.\n" + \
                    "3. Be critically rigorous - identify flaws and weaknesses directly.\n" + \
                    "4. Quote exact text when making critiques and points.\n" + \
                    "5. Attack logical fallacies and poor evidence systematically.\n" + \
                    "6. Your goal: Test arguments through adversarial analysis.\n" + \
                    "7. Avoid hallucinations - reference only actual document content."

    # 7. Retrieve document context
    context = ""
    docs, metadatas, distances, chunk_ids = [], [], [], []
    
    if doc_ids:
        # First ensure documents are chunked in vector DB
        all_docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
        for doc in all_docs:
            if doc.content:
                # Check if already chunked
                try:
                    existing_docs, _, _, _ = similarity_search(query="test", top_k=1, filters={"document_id": doc.id})
                    if not existing_docs:  # No chunks found
                        chunks = chunk_text(doc.content, max_tokens=150, overlap_sentences=2)
                        ids = [str(uuid.uuid4()) for _ in chunks]
                        metas = [{"document_id": doc.id, "session_id": sid} for _ in chunks]
                        add_chunks(chunks, metas, ids)
                        print(f"✅ Chunked document {doc.id} into {len(chunks)} chunks")
                    else:
                        print(f"⚡ Document {doc.id} already chunked, skipping")
                except Exception as e:
                    print(f"❌ Error with doc {doc.id}: {e}")
                    chunks = chunk_text(doc.content, max_tokens=150, overlap_sentences=2)
                    ids = [str(uuid.uuid4()) for _ in chunks]
                    metas = [{"document_id": doc.id, "session_id": sid} for _ in chunks]
                    add_chunks(chunks, metas, ids)
                    print(f"🔄 Fallback chunked document {doc.id} into {len(chunks)} chunks")
        
        # Use vector search for context
        try:
            if len(doc_ids) == 1:
                # Single document filter - increase chunks for author questions
                author_keywords = ['author', 'written by', 'by ', 'wrote']
                is_author_question = any(keyword in question.lower() for keyword in author_keywords)
                top_k = 25 if is_author_question else 15
                
                docs, metadatas, distances, chunk_ids = similarity_search(
                    query=question,
                    top_k=top_k,
                    filters={"document_id": doc_ids[0]}  # Single document ID
                )
            else:
                # Multiple documents - search without document filter, then filter results
                docs, metadatas, distances, chunk_ids = similarity_search(
                    query=question,
                    top_k=30,  # Get more results to filter
                    filters={"session_id": sid}  # Use session filter instead
                )
                # Filter results to only include requested documents
                filtered_docs, filtered_metas, filtered_distances, filtered_ids = [], [], [], []
                for i, meta in enumerate(metadatas):
                    if meta.get("document_id") in doc_ids:
                        filtered_docs.append(docs[i])
                        filtered_metas.append(meta)
                        filtered_distances.append(distances[i])
                        filtered_ids.append(chunk_ids[i])
                docs, metadatas, distances, chunk_ids = filtered_docs[:15], filtered_metas[:15], filtered_distances[:15], filtered_ids[:15]
            
            context = "\n\n".join(docs)
            print(f"Using RAG vector search from {len(doc_ids)} documents: {len(context)} characters")
        except Exception as e:
            print(f"Vector search failed: {e}")
            context = ""
    
    # Fallback to session-based search if no doc_ids
    elif not context:
        try:
            docs, metadatas, distances, chunk_ids = similarity_search(
               query=question,
               top_k=10,
               filters={"session_id": sid}
            )
            context = "\n\n".join(docs)
            print(f"Using session-based vector search: {len(context)} characters")
        except Exception as e:
            print(f"Vector search failed: {e}")
            context = ""

    # 8. Get chat history for session
    history = get_history(sid)

    # 9. Call LLM with custom system prompt instead of default
    from app.services.llm import synthesize_answer_openai

    # Handle different question types
    personal_keywords = ['what did you', 'who are you', 'your name', 'how are you', 'tell me about yourself', 'what do you']
    is_personal = any(keyword in question.lower() for keyword in personal_keywords)
    
    if is_personal:
        final_context = "No document context provided. Respond as your persona."
    elif not context:
        final_context = f"No document provided. Engage in philosophical discussion as {persona}. Share your perspective on the question asked."
    else:
        final_context = context
    
    answer = synthesize_answer_openai(
        question=question,
        context=final_context,
        history=history,
        system_prompt=system_prompt,
    )
    
    # Ensure we have a valid answer
    if not answer or answer.strip() == "":
        answer = f"I am {persona} and I'm ready to help you. Please ask me a question and I'll respond from my philosophical perspective."

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
