# app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.services.session import get_history, append_history
from app.schemas.rag import IngestResponse, QueryRequest, QueryResponse, SourceChunk, CreateSessionResponse
from app.services.ingestion import ingest_files
from app.services.retrieval import similarity_search
from app.services.llm import synthesize_answer_openai


router = APIRouter(prefix="/api/session", tags=["Rag"])
# Simple in-memory chat sessions
_SESSIONS: dict[str, List[dict]] = {}
@router.post("/")
def create_session():
    sid = str(uuid.uuid4())
    _SESSIONS[sid] = []
    return {"session_id": sid}