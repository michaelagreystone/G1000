"""
Shared vector store for all Fallon sub-agents.
Uses ChromaDB with the built-in ONNX all-MiniLM-L6-v2 embedding function —
no separate sentence-transformers or torch installation required.

Three collections:
  fallon_contracts    — chunked contract PDFs (loan, JV, construction, architect, lease)
  fallon_deal_data    — historical deal memos and pro forma summaries
  fallon_market_defaults — structured market assumption records by market + program type
"""

import os
import json
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# ── Paths ──────────────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STORE_PATH = os.path.join(_BASE_DIR, "vector_store")
_MARKET_DEFAULTS_PATH = os.path.join(_BASE_DIR, "data", "market_defaults", "market_defaults.json")

# Collection names — referenced by every agent, never hard-coded elsewhere
CONTRACTS_COLLECTION = "fallon_contracts"
DEAL_DATA_COLLECTION = "fallon_deal_data"
MARKET_DEFAULTS_COLLECTION = "fallon_market_defaults"

# ── Client & embedding function ────────────────────────────────────────────────
# Persistent client: data survives between app restarts
_client = chromadb.PersistentClient(path=_STORE_PATH)

# ChromaDB's built-in ONNX embedder (all-MiniLM-L6-v2, 384 dimensions).
# Model is cached in ~/.cache/chroma after first download — no re-download on restart.
_embedding_fn = DefaultEmbeddingFunction()


def get_collection(name: str) -> chromadb.Collection:
    """
    Return a ChromaDB collection by name, creating it if it doesn't exist yet.
    All three collections share the same embedding function so cross-collection
    similarity scores are directly comparable.

    Args:
        name: One of CONTRACTS_COLLECTION, DEAL_DATA_COLLECTION,
              or MARKET_DEFAULTS_COLLECTION.

    Returns:
        The ChromaDB Collection object.
    """
    return _client.get_or_create_collection(
        name=name,
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"},  # cosine distance — lower = more similar
    )


def add_documents(
    collection_name: str,
    texts: list[str],
    metadatas: list[dict],
    ids: list[str],
) -> dict:
    """
    Embed and upsert documents into a collection, skipping any that already exist.

    Deduplication is handled by checking existing IDs before upserting.
    Safe to call repeatedly — already-indexed documents are never double-embedded.

    Args:
        collection_name: Which collection to add documents to.
        texts:     List of text strings to embed and store.
        metadatas: List of metadata dicts, one per text. Must include at minimum
                   {"source": filename}. Additional keys are queryable via filters.
        ids:       Unique string IDs for each document chunk. Convention:
                   "{filename}_{chunk_index}" e.g. "loan_agreement_sample_042"

    Returns:
        dict with keys:
          "added"   — number of new documents ingested
          "skipped" — number of documents already in the collection
          "total"   — total documents now in the collection
    """
    if not texts:
        return {"added": 0, "skipped": 0, "total": _get_count(collection_name)}

    collection = get_collection(collection_name)

    # Check which IDs already exist to avoid re-embedding
    existing = set()
    try:
        existing_results = collection.get(ids=ids, include=[])
        existing = set(existing_results["ids"])
    except Exception:
        pass  # If the collection is empty, get() may raise — treat as no existing

    new_texts, new_metas, new_ids = [], [], []
    for text, meta, doc_id in zip(texts, metadatas, ids):
        if doc_id not in existing:
            new_texts.append(text)
            new_metas.append(meta)
            new_ids.append(doc_id)

    skipped = len(texts) - len(new_texts)

    if new_texts:
        collection.upsert(documents=new_texts, metadatas=new_metas, ids=new_ids)

    total = _get_count(collection_name)
    print(
        f"[vector_store] {collection_name}: "
        f"added {len(new_texts)}, skipped {skipped}, total {total}"
    )
    return {"added": len(new_texts), "skipped": skipped, "total": total}


def query_collection(
    collection_name: str,
    query_text: str,
    n_results: int = 5,
    where: dict | None = None,
) -> list[dict]:
    """
    Semantic search over a collection. Returns the top-n most similar chunks.

    Args:
        collection_name: Which collection to search.
        query_text:      Plain-English query string — embedded automatically.
        n_results:       Number of results to return. Default 5 gives enough
                         context without overloading the Claude prompt.
        where:           Optional ChromaDB metadata filter dict, e.g.:
                         {"doc_type": {"$eq": "loan_agreement"}}
                         Used by the contract agent to scope searches to a
                         specific contract type.

    Returns:
        List of dicts, sorted by relevance (most relevant first):
          {
            "text":       str   — the chunk text,
            "metadata":   dict  — source filename, doc_type, chunk_index, etc.,
            "distance":   float — cosine distance (lower = more similar),
            "relevance":  str   — "high" / "medium" / "low" classification
          }
    """
    collection = get_collection(collection_name)

    # Guard: can't query an empty collection
    if collection.count() == 0:
        return []

    # Cap n_results at the actual collection size to avoid ChromaDB errors
    actual_n = min(n_results, collection.count())

    query_kwargs = {
        "query_texts": [query_text],
        "n_results": actual_n,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where

    results = collection.query(**query_kwargs)

    # Unpack ChromaDB's nested list structure (one query → one result set)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    output = []
    for doc, meta, dist in zip(docs, metas, distances):
        output.append(
            {
                "text": doc,
                "metadata": meta,
                "distance": round(dist, 4),
                "relevance": _classify_relevance(dist),
            }
        )

    return output


def get_collection_counts() -> dict:
    """
    Return document counts for all three collections.
    Used by the Streamlit sidebar to show how many documents are indexed.

    Returns:
        {"fallon_contracts": int, "fallon_deal_data": int, "fallon_market_defaults": int}
    """
    return {
        CONTRACTS_COLLECTION: _get_count(CONTRACTS_COLLECTION),
        DEAL_DATA_COLLECTION: _get_count(DEAL_DATA_COLLECTION),
        MARKET_DEFAULTS_COLLECTION: _get_count(MARKET_DEFAULTS_COLLECTION),
    }


def get_market_defaults(market: str, program_type: str) -> dict | None:
    """
    Direct lookup of market defaults by market name and program type.
    Bypasses vector search for precise, exact-match retrieval of numeric assumptions.

    The Financial Model sub-agent uses this for exact number injection.
    Vector search is used for contextual retrieval — this is for precise values.

    Args:
        market:       e.g. "charlotte", "nashville", "boston"
        program_type: e.g. "multifamily", "office", "hotel", "mixed_use"

    Returns:
        Dict of assumption values for that market/program, or None if not found.
        Falls back to "national_average" if the specific market isn't in the file.
    """
    if not os.path.exists(_MARKET_DEFAULTS_PATH):
        return None

    with open(_MARKET_DEFAULTS_PATH, "r") as f:
        defaults = json.load(f)

    market_key = market.lower().strip()
    program_key = program_type.lower().strip().replace("-", "_").replace(" ", "_")

    # Try exact match first
    if market_key in defaults and program_key in defaults[market_key]:
        return defaults[market_key][program_key]

    # Fall back to national average if market not found
    if "national_average" in defaults and program_key in defaults["national_average"]:
        data = defaults["national_average"][program_key].copy()
        data["_fallback"] = True
        data["_fallback_reason"] = f"No data for market '{market}' — using national averages. Verify with local broker."
        return data

    return None


# ── Internal helpers ────────────────────────────────────────────────────────────

def _get_count(collection_name: str) -> int:
    """Return the number of documents in a collection, 0 if it doesn't exist."""
    try:
        return get_collection(collection_name).count()
    except Exception:
        return 0


def _classify_relevance(distance: float) -> str:
    """
    Convert a cosine distance score into a human-readable relevance label.
    Used by sub-agents to filter low-quality retrievals before passing to Claude.

    Thresholds calibrated for all-MiniLM-L6-v2 on legal/financial text:
      < 0.30  → high    (very similar — strong match)
      0.30–0.55 → medium (related — probably useful)
      > 0.55  → low     (weak match — use with caution)
    """
    if distance < 0.30:
        return "high"
    elif distance < 0.55:
        return "medium"
    else:
        return "low"
