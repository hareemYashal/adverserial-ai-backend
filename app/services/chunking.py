from typing import List
import re

def _simple_sentence_tokenize(text: str) -> List[str]:
    """
    Simple sentence tokenizer that doesn't require NLTK downloads.
    Splits text on sentence-ending punctuation followed by whitespace.
    """
    # Pattern to match sentence endings: . ! ? followed by whitespace or end of string
    sentence_pattern = r'[.!?]+\s*'
    sentences = re.split(sentence_pattern, text)
    
    # Clean up sentences and filter out empty ones
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # If no sentences found, return the whole text as one sentence
    if not sentences:
        return [text.strip()]
    
    return sentences

def _get_sentence_tokenizer():
    """Get the best available sentence tokenizer."""
    try:
        import nltk
        # Try to use NLTK if available
        try:
            from nltk.tokenize import sent_tokenize
            # Test if it works
            sent_tokenize("Test sentence.")
            return sent_tokenize
        except (ImportError, LookupError):
            pass
    except ImportError:
        pass
    
    # Fall back to simple regex-based tokenizer
    return _simple_sentence_tokenize

# Initialize the sentence tokenizer
sent_tokenize = _get_sentence_tokenizer() 
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
