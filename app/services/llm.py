from typing import Optional, List, Dict
from app.config import OPENAI_MODEL,OPENAI_API_KEY
import os


def synthesize_answer_openai(
    question: str,
    context: str,
    system_prompt: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> Optional[str]:
    if not os.getenv("OPENAI_API_KEY"):
        print("OpenAI API key is missing!")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv(OPENAI_API_KEY))

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({
            "role": "user",
            "content": f"Question: {question}\n\nRelevant context:\n{context}"
        })

        print("Sending messages to OpenAI:")
        for msg in messages:
            print(f"  {msg['role']}: {msg['content'][:200]}")  # preview only

        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=messages,
            temperature=0.2,
        )

        answer = resp.choices[0].message.content.strip()
        print(f"OpenAI returned answer: {answer}")
        return answer

    except Exception as e:
        print(f"OpenAI synthesis failed with error: {e}")
        return None