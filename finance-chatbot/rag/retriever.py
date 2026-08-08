"""
Retrieval layer for the RAG pipeline.

Queries the persistent Chroma vector database built by ingest.py and
returns the top-k most relevant document chunks for a given user question.
"""

from pathlib import Path

import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_ROOT / "rag" / "chroma_db"
COLLECTION_NAME = "finance_docs"

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(DB_DIR))
        _collection = _client.get_or_create_collection(COLLECTION_NAME)
    return _collection


def retrieve(query: str, top_k: int = 3):
    """
    Returns a list of {"text": str, "source": str, "distance": float}
    for the top_k chunks most relevant to `query`. Returns [] if the index
    hasn't been built yet (e.g. rag/ingest.py hasn't been run).
    """
    collection = _get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return [
        {"text": doc, "source": meta.get("source", "unknown"), "distance": dist}
        for doc, meta, dist in zip(docs, metas, distances)
    ]


def format_context(chunks) -> str:
    """Formats retrieved chunks into a block suitable for prompt injection."""
    if not chunks:
        return ""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[Source {i}: {chunk['source']}]\n{chunk['text']}")
    return "\n\n".join(parts)
