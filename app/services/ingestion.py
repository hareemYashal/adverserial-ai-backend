import os
import uuid
from typing import List, Tuple
from app.services.chunking import chunk_text
from app.services.retrieval import add_chunks
import nltk

# Download punkt if not already present
nltk.download("punkt")

def ingest_files(self, file_path: str, file_type: str) -> str:
    total_chunks = 0
    for path in paths:
        chunks = chunk_text(content, max_tokens=150, overlap_sentences=2)
        ids = [f"{uuid.uuid4()}" for _ in chunks]
        metas = [{"source": os.path.basename(path), "path": os.path.abspath(path), "chunk": i} for i, _ in enumerate(chunks)]
        total_chunks += add_chunks(chunks, metas, ids)
    return len(paths), total_chunks
