from typing import List
import nltk
nltk.download('punkt')       # usual tokenizer
nltk.download('punkt_tab') 
from nltk.tokenize import sent_tokenize 
def chunk_text(
    text: str, 
    max_tokens: int = 150,  # approximate tokens per chunk
    overlap_sentences: int = 2
) -> List[str]:
    """
    Chunk text based on sentences (semantic chunks) instead of character count.
    
    Args:
        text: Input string to chunk.
        max_tokens: Approximate number of words per chunk (can tweak for LLM input).
        overlap_sentences: Number of sentences to overlap between consecutive chunks.
        
    Returns:
        List of chunks, each containing complete sentences.
    """
    text = text.strip()
    if not text:
        return []

    sentences = sent_tokenize(text)
    chunks = []
    i = 0
    n = len(sentences)

    while i < n:
        chunk_sentences = []
        tokens_count = 0
        j = i

        # Build chunk until max_tokens reached
        while j < n and tokens_count + len(sentences[j].split()) <= max_tokens:
            chunk_sentences.append(sentences[j])
            tokens_count += len(sentences[j].split())
            j += 1

        # If no sentence added (very long sentence), force add one
        if not chunk_sentences:
            chunk_sentences.append(sentences[j])
            j += 1

        chunks.append(" ".join(chunk_sentences))
        # Move to next chunk with overlap
        i = max(i + 1, j - overlap_sentences)

    return chunks
