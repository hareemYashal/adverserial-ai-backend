from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.session import get_history, append_history
from app.services.llm import synthesize_answer_openai
import uuid

router = APIRouter(prefix="/api/persona-chat", tags=["Chat"])

@router.post("/simple")
async def chat_simple(
    question: str = Form(...),
    persona: str = Form(...),   # persona name comes from frontend
    session_id: str = Form(None),
    db: Session = Depends(get_db)
):
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    # Dynamically build system prompt instead of static lookup
    system_prompt = (
        f"You are now impersonating {persona}. "
        f"Adopt the communication style, personality traits, and reasoning approach of {persona}. "
        f"Always stay in character and respond as if you are {persona}."
    )

    sid = session_id or str(uuid.uuid4())
    history = get_history(sid)

    try:
        # Call the LLM with dynamic persona prompt
        answer = synthesize_answer_openai(
            question=question,
            context="",            # keep empty unless docs are used
            history=history,
            system_prompt=system_prompt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    append_history(sid, "user", question)
    append_history(sid, "assistant", answer or "No answer available.")

    return {
        "answer": answer,
        "session_id": sid,
        "persona": persona,
        "used_llm": bool(answer)
    }
