"""
Document ingestion for the RAG pipeline.

Reads every .txt file in data/finance_docs/, splits it into overlapping
word chunks, embeds each chunk (via ChromaDB's built-in local embedding
function — no external API needed), and stores it in a persistent local
Chroma vector database.

Run this once before starting the backend, and again any time you add or
change files in data/finance_docs/:

    python rag/ingest.py
"""

from pathlib import Path

import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "finance_docs"
DB_DIR = PROJECT_ROOT / "rag" / "chroma_db"
COLLECTION_NAME = "finance_docs"

CHUNK_SIZE = 180   # words per chunk
CHUNK_OVERLAP = 30  # words of overlap between consecutive chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    step = max(chunk_size - overlap, 1)
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += step
    return chunks


def build_index() -> int:
    """Rebuild the vector index from scratch. Returns number of chunks indexed."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB_DIR))

    # Start clean each time this script runs, so re-running it after editing
    # a doc doesn't leave stale chunks behind.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    files = sorted(DATA_DIR.glob("*.txt"))
    if not files:
        print(f"No .txt files found in {DATA_DIR}")
        return 0

    total_chunks = 0
    for file in files:
        text = file.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        if not chunks:
            continue
        ids = [f"{file.stem}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": file.name, "chunk_index": i} for i in range(len(chunks))]
        collection.add(ids=ids, documents=chunks, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"  {file.name}: {len(chunks)} chunks")

    print(f"\nIndexed {total_chunks} chunks from {len(files)} files into {DB_DIR}")
    return total_chunks


if __name__ == "__main__":
    build_index()
