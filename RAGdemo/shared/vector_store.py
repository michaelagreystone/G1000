"""
In-memory vector store for Contract Reviewer.
Uses ChromaDB with built-in ONNX all-MiniLM-L6-v2 embeddings.
Documents exist only for the session — nothing persists to disk.
"""

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

COLLECTION_NAME = "user_contracts"

# In-memory client — all data is lost when the process ends
_client = chromadb.Client()
_embedding_fn = DefaultEmbeddingFunction()


def get_collection() -> chromadb.Collection:
    """Return the contracts collection, creating it if needed."""
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection():
    """Delete and recreate the collection (used when uploading a new contract)."""
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return get_collection()


def add_documents(texts: list[str], metadatas: list[dict], ids: list[str]) -> int:
    """Embed and store document chunks. Returns number added."""
    if not texts:
        return 0
    collection = get_collection()
    collection.upsert(documents=texts, metadatas=metadatas, ids=ids)
    return len(texts)


def query(query_text: str, n_results: int = 5) -> list[dict]:
    """Semantic search over stored contract chunks."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    actual_n = min(n_results, collection.count())
    results = collection.query(
        query_texts=[query_text],
        n_results=actual_n,
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    output = []
    for doc, meta, dist in zip(docs, metas, distances):
        output.append({
            "text": doc,
            "metadata": meta,
            "distance": round(dist, 4),
        })
    return output


def get_count() -> int:
    """Return number of chunks in the collection."""
    try:
        return get_collection().count()
    except Exception:
        return 0
