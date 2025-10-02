from typing import List, Tuple, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from chromadb.api import ClientAPI, Collection
from app.config import CHROMA_DIR, CHROMA_COLLECTION, EMBEDDING_MODEL

# Singleton Chroma client + collection
_client: Optional[ClientAPI] = None
_collection: Optional[Collection] = None
_embedder = None


def get_chroma_client() -> ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=ChromaSettings(allow_reset=False),
        )
    return _client


def get_collection() -> Collection:
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(name=CHROMA_COLLECTION)
    return _collection


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
    return _embedder


def add_chunks(chunks: List[str], metadatas: List[dict], ids: List[str]) -> int:
    col = get_collection()
    embed = get_embedder()
    
    print(f"🔧 ChromaDB: Adding {len(chunks)} chunks to collection '{CHROMA_COLLECTION}' at '{CHROMA_DIR}'")
    
    col.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids,
        embeddings=embed(chunks),
    )
    
    # Verify chunks were added
    total_count = col.count()
    print(f"✅ ChromaDB: Total chunks in collection: {total_count}")
    
    return len(chunks)


def similarity_search(
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> Tuple[List[str], List[dict], List[float], List[str]]:
    col = get_collection()
    embed = get_embedder()
    
    total_count = col.count()
    print(f"🔍 ChromaDB: Searching in collection with {total_count} total chunks, filters: {filters}")

    q_emb = embed([query])

    res = col.query(
        query_embeddings=q_emb,
        n_results=top_k,
        where=filters or {},
        include=["documents", "metadatas", "distances"],  # ✅ REMOVE "ids"
    )

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    ids = res.get("ids", [[]])[0]  # ✅ This still works (Chroma always returns "ids")
    
    print(f"✅ ChromaDB: Found {len(docs)} matching chunks")

    return docs, metas, dists, ids