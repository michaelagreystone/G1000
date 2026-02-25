"""
Ingest contract provision reference documents into a dedicated ChromaDB collection.

Reads every .txt file in data/contract_provisions/ and data/market_research/,
chunks them, and upserts into the vector store. These documents power the RAG
agent's ability to answer questions about RE PE deal structures, contract
clauses, and market conditions.

Usage: python "FallonPrototype/Financial Model/shared/ingest_contract_provisions.py"
"""

import os
import sys

_FM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROTO_DIR = os.path.dirname(_FM_DIR)
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from langchain_text_splitters import RecursiveCharacterTextSplitter

from FallonPrototype.shared.vector_store import add_documents, get_collection

# Collection names for the new data
CONTRACTS_PROVISIONS_COLLECTION = "fallon_contract_provisions"
MARKET_RESEARCH_COLLECTION = "fallon_market_research"

_CONTRACT_DIR = os.path.join(_FM_DIR, "data", "contract_provisions")
_RESEARCH_DIR = os.path.join(_FM_DIR, "data", "market_research")

# Metadata mapping for contract provision files
_CONTRACT_METADATA = {
    "jv_lp_gp_agreements": {
        "doc_type": "contract_provisions",
        "topic": "jv_lp_gp_agreement",
        "subtopics": "waterfall,promote,clawback,capital_call,gp_removal,key_person,transfer_restrictions",
    },
    "land_purchase_agreements": {
        "doc_type": "contract_provisions",
        "topic": "land_purchase",
        "subtopics": "earnest_money,due_diligence,environmental,entitlement,seller_financing,ground_lease,option,closing",
    },
    "construction_contracts": {
        "doc_type": "contract_provisions",
        "topic": "construction_contract",
        "subtopics": "gmp,change_order,retainage,liquidated_damages,substantial_completion,performance_bond,termination",
    },
    "commercial_lease_provisions": {
        "doc_type": "contract_provisions",
        "topic": "commercial_lease",
        "subtopics": "nnn,cam,ti_allowance,co_tenancy,exclusivity,snda,estoppel,renewal,assignment",
    },
    "mezzanine_preferred_equity": {
        "doc_type": "contract_provisions",
        "topic": "mezzanine_preferred_equity",
        "subtopics": "intercreditor,subordination,conversion,pik,equity_kicker,default,foreclosure",
    },
    "promote_carried_interest_structures": {
        "doc_type": "contract_provisions",
        "topic": "promote_structures",
        "subtopics": "waterfall,irr_hurdle,moic,catch_up,lookback,clawback,distribution,developer_fee",
    },
}

# Larger chunks for reference docs — they have section structure we want to preserve
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=250,
    separators=["\n═══", "\n\n", "\n", ". ", " ", ""],
)


def _parse_metadata(filename: str, doc_type: str) -> dict:
    """Extract metadata from filename."""
    stem = os.path.splitext(filename)[0]
    if stem in _CONTRACT_METADATA:
        return _CONTRACT_METADATA[stem].copy()
    return {
        "doc_type": doc_type,
        "topic": stem,
        "subtopics": "",
    }


def _ingest_directory(directory: str, collection_name: str, doc_type: str) -> dict:
    """Ingest all .txt files from a directory into a collection."""
    if not os.path.isdir(directory):
        print(f"  Directory not found: {directory}")
        return {"files": 0, "chunks": 0}

    txt_files = sorted(f for f in os.listdir(directory) if f.endswith(".txt"))
    if not txt_files:
        print(f"  No .txt files found in {os.path.basename(directory)}/")
        return {"files": 0, "chunks": 0}

    # Ensure collection exists
    get_collection(collection_name)

    all_texts = []
    all_metadatas = []
    all_ids = []
    total_files = 0

    for filename in txt_files:
        filepath = os.path.join(directory, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            continue

        chunks = _splitter.split_text(content)
        base_meta = _parse_metadata(filename, doc_type)
        stem = os.path.splitext(filename)[0]

        for i, chunk in enumerate(chunks):
            chunk_id = f"{collection_name}_{stem}_{i:03d}"
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
        print(f"  {filename}: {len(chunks)} chunks ({len(content)} chars)")

    if all_texts:
        result = add_documents(collection_name, all_texts, all_metadatas, all_ids)
        print(f"  Total: {total_files} files, {result['added']} new, "
              f"{result['skipped']} skipped, {result['total']} in collection")
    else:
        result = {"added": 0, "total": 0}

    return {"files": total_files, "chunks": len(all_texts)}


def ingest_contract_provisions() -> dict:
    """Ingest contract provision reference documents."""
    return _ingest_directory(_CONTRACT_DIR, CONTRACTS_PROVISIONS_COLLECTION, "contract_provisions")


def ingest_market_research() -> dict:
    """Ingest market research reference documents."""
    return _ingest_directory(_RESEARCH_DIR, MARKET_RESEARCH_COLLECTION, "market_research")


def main():
    print("=" * 60)
    print("CONTRACT PROVISIONS & MARKET RESEARCH INGESTION")
    print("=" * 60)

    print("\n--- Contract Provisions ---")
    cp_result = ingest_contract_provisions()

    print("\n--- Market Research ---")
    mr_result = ingest_market_research()

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print(f"  Contract provisions: {cp_result['chunks']} chunks across {cp_result['files']} files")
    print(f"  Market research:     {mr_result['chunks']} chunks across {mr_result['files']} files")
    print("=" * 60)


if __name__ == "__main__":
    main()
