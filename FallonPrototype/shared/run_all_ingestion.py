"""
Combined ingestion runner — runs all data ingestion pipelines in sequence.

Usage: python -m FallonPrototype.shared.run_all_ingestion
"""

import os
import sys

_SHARED_DIR = os.path.dirname(os.path.abspath(__file__))
_PROTO_DIR = os.path.dirname(_SHARED_DIR)
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from langchain_text_splitters import RecursiveCharacterTextSplitter

from FallonPrototype.shared.ingest_deal_data import ingest_deal_data
from FallonPrototype.shared.ingest_market_defaults import ingest_market_defaults
from FallonPrototype.shared.vector_store import (
    add_documents, get_collection_counts, DEAL_DATA_COLLECTION
)


def ingest_market_research() -> dict:
    """Ingest market research files into deal data collection."""
    research_dir = os.path.join(_PROTO_DIR, "Financial Model", "data", "market_research")
    
    if not os.path.isdir(research_dir):
        print(f"[ingest_market_research] Directory not found: {research_dir}")
        return {"files": 0, "chunks": 0}
    
    txt_files = sorted(f for f in os.listdir(research_dir) if f.endswith(".txt"))
    if not txt_files:
        print("[ingest_market_research] No .txt files found")
        return {"files": 0, "chunks": 0}
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    all_texts = []
    all_metadatas = []
    all_ids = []
    
    for filename in txt_files:
        filepath = os.path.join(research_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        if not content:
            continue
        
        chunks = splitter.split_text(content)
        stem = os.path.splitext(filename)[0]
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"research_{stem}_{i:03d}"
            meta = {
                "source": filename,
                "doc_type": "market_research",
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            all_texts.append(chunk)
            all_metadatas.append(meta)
            all_ids.append(chunk_id)
        
        print(f"  {filename}: {len(chunks)} chunks")
    
    if all_texts:
        result = add_documents(DEAL_DATA_COLLECTION, all_texts, all_metadatas, all_ids)
        print(f"\n[ingest_market_research] Done: {len(txt_files)} files, "
              f"{result['added']} new chunks")
    
    return {"files": len(txt_files), "chunks": len(all_texts)}


def ingest_contract_provisions() -> dict:
    """Ingest contract provision reference docs."""
    provisions_dir = os.path.join(_PROTO_DIR, "Financial Model", "data", "contract_provisions")
    
    if not os.path.isdir(provisions_dir):
        print(f"[ingest_contract_provisions] Directory not found: {provisions_dir}")
        return {"files": 0, "chunks": 0}
    
    txt_files = sorted(f for f in os.listdir(provisions_dir) if f.endswith(".txt"))
    if not txt_files:
        print("[ingest_contract_provisions] No .txt files found")
        return {"files": 0, "chunks": 0}
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    all_texts = []
    all_metadatas = []
    all_ids = []
    
    for filename in txt_files:
        filepath = os.path.join(provisions_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        if not content:
            continue
        
        chunks = splitter.split_text(content)
        stem = os.path.splitext(filename)[0]
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"contract_{stem}_{i:03d}"
            meta = {
                "source": filename,
                "doc_type": "contract_provision",
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            all_texts.append(chunk)
            all_metadatas.append(meta)
            all_ids.append(chunk_id)
        
        print(f"  {filename}: {len(chunks)} chunks")
    
    if all_texts:
        result = add_documents(DEAL_DATA_COLLECTION, all_texts, all_metadatas, all_ids)
        print(f"\n[ingest_contract_provisions] Done: {len(txt_files)} files, "
              f"{result['added']} new chunks")
    
    return {"files": len(txt_files), "chunks": len(all_texts)}


def main():
    print("=" * 60)
    print("FALLON FINANCIAL MODEL - FULL DATA INGESTION")
    print("=" * 60)

    print("\n--- Phase 1: Deal Data ---")
    deal_result = ingest_deal_data()

    print("\n--- Phase 2: Market Defaults ---")
    defaults_result = ingest_market_defaults()

    print("\n--- Phase 3: Market Research ---")
    research_result = ingest_market_research()

    print("\n--- Phase 4: Contract Provisions ---")
    contract_result = ingest_contract_provisions()

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)

    counts = get_collection_counts()
    print(f"  fallon_deal_data:       {counts.get('fallon_deal_data', 0)} chunks")
    print(f"  fallon_market_defaults: {counts.get('fallon_market_defaults', 0)} records")
    print("=" * 60)


if __name__ == "__main__":
    main()
