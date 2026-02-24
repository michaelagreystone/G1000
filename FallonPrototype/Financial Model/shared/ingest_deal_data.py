"""
Ingest historical deal data text files into the fallon_deal_data ChromaDB collection.

Reads every .txt file in data/deal_data/, chunks them using RecursiveCharacterTextSplitter,
and upserts into the vector store with structured metadata.

Usage: python -m FallonPrototype.Financial_Model.shared.ingest_deal_data
"""

import os
import sys

# Add FallonPrototype root to path so we can import shared modules
_FM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROTO_DIR = os.path.dirname(_FM_DIR)
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from langchain_text_splitters import RecursiveCharacterTextSplitter

from FallonPrototype.shared.vector_store import add_documents, DEAL_DATA_COLLECTION

_DEAL_DATA_DIR = os.path.join(_FM_DIR, "data", "deal_data")

# Metadata mapping: filename prefix -> deal metadata
# Convention: {market}_{deal_type}_overview.txt
_DEAL_METADATA = {
    "nashville_mixed_use_overview": {
        "deal_type": "mixed_use",
        "market": "nashville",
        "deal_status": "completed",
        "approx_year": "2023",
        "program_mix": "multifamily,retail",
    },
    "charlotte_multifamily_overview": {
        "deal_type": "multifamily",
        "market": "charlotte",
        "deal_status": "completed",
        "approx_year": "2023",
        "program_mix": "multifamily",
    },
    "boston_office_overview": {
        "deal_type": "office",
        "market": "boston",
        "deal_status": "active",
        "approx_year": "2024",
        "program_mix": "office",
    },
    "fanpier_residential_overview": {
        "deal_type": "condo",
        "market": "boston",
        "deal_status": "completed",
        "approx_year": "2022",
        "program_mix": "condo",
    },
}

# Larger chunks for deal memos — denser prose needs more context preserved
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def _parse_metadata_from_filename(filename: str) -> dict:
    """Extract metadata from filename, falling back to filename-based parsing."""
    stem = os.path.splitext(filename)[0]

    if stem in _DEAL_METADATA:
        return _DEAL_METADATA[stem].copy()

    # Fallback: parse from naming convention {market}_{deal_type}_overview
    parts = stem.replace("_overview", "").split("_", 1)
    market = parts[0] if len(parts) > 0 else "unknown"
    deal_type = parts[1] if len(parts) > 1 else "unknown"

    return {
        "deal_type": deal_type,
        "market": market,
        "deal_status": "unknown",
        "approx_year": "unknown",
        "program_mix": deal_type,
    }


def ingest_deal_data() -> dict:
    """Ingest all .txt files from data/deal_data/ into the vector store."""
    if not os.path.isdir(_DEAL_DATA_DIR):
        print(f"[ingest_deal_data] Directory not found: {_DEAL_DATA_DIR}")
        return {"files": 0, "chunks": 0}

    txt_files = sorted(f for f in os.listdir(_DEAL_DATA_DIR) if f.endswith(".txt"))
    if not txt_files:
        print("[ingest_deal_data] No .txt files found in data/deal_data/")
        return {"files": 0, "chunks": 0}

    all_texts = []
    all_metadatas = []
    all_ids = []
    total_files = 0

    for filename in txt_files:
        filepath = os.path.join(_DEAL_DATA_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            print(f"  Skipping empty file: {filename}")
            continue

        chunks = _splitter.split_text(content)
        base_meta = _parse_metadata_from_filename(filename)
        stem = os.path.splitext(filename)[0]

        for i, chunk in enumerate(chunks):
            chunk_id = f"{stem}_{i:03d}"
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
        result = add_documents(DEAL_DATA_COLLECTION, all_texts, all_metadatas, all_ids)
        print(f"\n[ingest_deal_data] Done: {total_files} files, "
              f"{result['added']} new chunks, {result['skipped']} skipped, "
              f"{result['total']} total in collection")
    else:
        result = {"added": 0, "total": 0}

    return {"files": total_files, "chunks": len(all_texts)}


def main():
    print("=" * 60)
    print("DEAL DATA INGESTION")
    print("=" * 60)
    ingest_deal_data()
    print("=" * 60)


if __name__ == "__main__":
    main()
