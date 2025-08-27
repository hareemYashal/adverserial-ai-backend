from typing import Dict, List
from typing import List, Optional
_SESSIONS: dict[str, List[dict]] = {}
def synthesize_answer_openai(
    question: str,
    context: str,
    history: Optional[List[dict]] = None
) -> Optional[str]:
    if not settings.OPENAI_API_KEY:
        return None

    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    messages = [
        {"role": "system", "content": _DEF_SUMMARY_PROMPT}
    ]

    # Include previous conversation
    if history:
        messages.extend(history)

    # Add latest user question + retrieved context
    messages.append({
        "role": "user",
        "content": f"Question: {question}\n\nRelevant context:\n{context}"
    })

    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()


def get_history(session_id: str) -> List[dict]:
    return _SESSIONS.get(session_id, [])

def append_history(session_id: str, role: str, content: str):
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = []
    _SESSIONS[session_id].append({"role": role, "content": content})

def reset_history(session_id: str):
    _SESSIONS[session_id] = []
