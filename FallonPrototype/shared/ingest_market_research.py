"""
Ingest market research documents into the fallon_market_research ChromaDB collection.

Reads .txt files from Financial Model/data/market_research/, chunks them,
and upserts into the vector store with structured metadata.

Usage: python -m FallonPrototype.shared.ingest_market_research
"""

import os
import sys

_SHARED_DIR = os.path.dirname(os.path.abspath(__file__))
_PROTO_DIR = os.path.dirname(_SHARED_DIR)
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from langchain_text_splitters import RecursiveCharacterTextSplitter

from FallonPrototype.shared.vector_store import add_documents, MARKET_RESEARCH_COLLECTION

_MARKET_RESEARCH_DIR = os.path.join(_PROTO_DIR, "Financial Model", "data", "market_research")

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def _parse_metadata_from_filename(filename: str) -> dict:
    """Extract metadata from market research filename."""
    stem = os.path.splitext(filename)[0].lower()
    
    # Detect markets mentioned in filename or content
    markets = []
    for market in ["boston", "charlotte", "nashville", "national"]:
        if market in stem:
            markets.append(market)
    
    # Detect document type
    doc_type = "market_research"
    if "cap_rate" in stem:
        doc_type = "cap_rate_report"
    elif "construction" in stem:
        doc_type = "construction_outlook"
    elif "hotel" in stem:
        doc_type = "hotel_outlook"
    elif "market_data" in stem:
        doc_type = "market_data"
    
    return {
        "doc_type": doc_type,
        "markets": ",".join(markets) if markets else "national",
        "source_type": "market_research",
    }


def ingest_market_research() -> dict:
    """Ingest all .txt files from market_research/ into the vector store."""
    if not os.path.isdir(_MARKET_RESEARCH_DIR):
        print(f"[ingest_market_research] Directory not found: {_MARKET_RESEARCH_DIR}")
        return {"files": 0, "chunks": 0}

    txt_files = sorted(f for f in os.listdir(_MARKET_RESEARCH_DIR) if f.endswith(".txt"))
    if not txt_files:
        print("[ingest_market_research] No .txt files found")
        return {"files": 0, "chunks": 0}

    all_texts = []
    all_metadatas = []
    all_ids = []
    total_files = 0

    for filename in txt_files:
        filepath = os.path.join(_MARKET_RESEARCH_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            print(f"  Skipping empty file: {filename}")
            continue

        chunks = _splitter.split_text(content)
        base_meta = _parse_metadata_from_filename(filename)
        stem = os.path.splitext(filename)[0]

        for i, chunk in enumerate(chunks):
            chunk_id = f"research_{stem}_{i:03d}"
            meta = {
                **base_meta,
                "source": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            all_texts.append(chunk)
            all_metadatas.append(meta)
            all_ids.append(chunk_id)

        total_files += 1
        print(f"  {filename}: {len(chunks)} chunks")

    if all_texts:
        result = add_documents(MARKET_RESEARCH_COLLECTION, all_texts, all_metadatas, all_ids)
        print(f"\n[ingest_market_research] Done: {total_files} files, "
              f"{result['added']} new chunks, {result['skipped']} skipped, "
              f"{result['total']} total in collection")
    else:
        result = {"added": 0, "total": 0}

    return {"files": total_files, "chunks": len(all_texts)}


def main():
    print("=" * 60)
    print("MARKET RESEARCH INGESTION")
    print("=" * 60)
    ingest_market_research()
    print("=" * 60)


if __name__ == "__main__":
    main()
