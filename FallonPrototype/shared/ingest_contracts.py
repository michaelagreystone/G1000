"""
Ingest contract documents with Claude-based structured extraction.

Reads contract files (.txt, .pdf) from data/contracts/, extracts structured
metadata using Claude, and upserts into the fallon_contracts ChromaDB collection.

Usage: python -m FallonPrototype.shared.ingest_contracts
"""

import os
import sys
import json
from datetime import datetime

_SHARED_DIR = os.path.dirname(os.path.abspath(__file__))
_PROTO_DIR = os.path.dirname(_SHARED_DIR)
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from langchain_text_splitters import RecursiveCharacterTextSplitter

from FallonPrototype.shared.vector_store import (
    add_documents,
    CONTRACTS_COLLECTION,
    DEAL_DATA_COLLECTION,
)
from FallonPrototype.shared.claude_client import call_claude
from FallonPrototype.shared.contract_models import (
    ExtractedContract,
    CONTRACT_TYPES,
    contract_to_metadata,
    contract_to_searchable_text,
)

_CONTRACTS_DIR = os.path.join(_PROTO_DIR, "data", "contracts")

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)

# ═══════════════════════════════════════════════════════════════════════════════
# Extraction System Prompt
# ═══════════════════════════════════════════════════════════════════════════════

EXTRACTION_PROMPT = f"""You are a legal document analyst specializing in real estate contracts. Extract structured information from the following contract.

Return a JSON object with these fields:
- summary: High-level summary (2-3 sentences, no pronouns)
- contract_type: One of {CONTRACT_TYPES}
- parties: Array of objects with name, role, and optional location (city, state, country)
- effective_date: YYYY-MM-DD format or null
- end_date: YYYY-MM-DD format or null
- duration: ISO 8601 duration (e.g., P3Y for 3 years) or null
- contract_scope: Description of scope, rights, duties
- total_amount: Total contract value as number (no currency symbols) or null
- monetary_values: Array of {{amount, currency, description}} for all monetary values
- governing_law: {{state, country}} or null
- clauses: Array of {{summary, clause_type, key_terms}} for key clauses
- property_address: Address of property if applicable
- property_type: multifamily, office, retail, hotel, mixed_use, etc.
- interest_rate: Rate as decimal (e.g., 0.05 for 5%) or null
- loan_to_value: LTV ratio as decimal or null

Rules:
1. Extract ONLY information explicitly stated in the document
2. Use null for fields not found in the document
3. For dates, convert to YYYY-MM-DD format
4. For monetary values, extract the raw number without currency symbols
5. Be precise with party roles (borrower, lender, landlord, tenant, developer, investor, etc.)

Return ONLY valid JSON, no other text."""


def extract_contract_metadata(contract_text: str) -> dict | None:
    """
    Use Claude to extract structured metadata from contract text.
    Returns a dict or None if extraction fails.
    """
    response = call_claude(
        EXTRACTION_PROMPT,
        f"CONTRACT DOCUMENT:\n\n{contract_text[:15000]}",  # Limit to avoid token overflow
        max_tokens=2000,
    )
    
    if response.startswith("ERROR:"):
        print(f"  [extraction] Claude error: {response}")
        return None
    
    # Parse JSON from response
    try:
        # Handle markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        return json.loads(response.strip())
    except json.JSONDecodeError as e:
        print(f"  [extraction] JSON parse error: {e}")
        print(f"  Response was: {response[:500]}...")
        return None


def read_contract_file(filepath: str) -> str | None:
    """Read contract content from file (supports .txt and basic .pdf)."""
    _, ext = os.path.splitext(filepath)
    
    if ext.lower() == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    
    elif ext.lower() == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except ImportError:
            print(f"  [warning] pypdf not installed, skipping PDF: {filepath}")
            return None
        except Exception as e:
            print(f"  [error] Failed to read PDF {filepath}: {e}")
            return None
    
    return None


def ingest_contracts(extract_metadata: bool = True) -> dict:
    """
    Ingest all contract files from data/contracts/ into the vector store.
    
    Args:
        extract_metadata: If True, use Claude to extract structured metadata.
                         If False, use basic filename-based metadata only.
    
    Returns:
        Dict with files processed, chunks added, and extraction stats.
    """
    if not os.path.isdir(_CONTRACTS_DIR):
        os.makedirs(_CONTRACTS_DIR, exist_ok=True)
        print(f"[ingest_contracts] Created directory: {_CONTRACTS_DIR}")
        return {"files": 0, "chunks": 0, "extracted": 0}
    
    # Find all contract files
    files = sorted(
        f for f in os.listdir(_CONTRACTS_DIR)
        if f.endswith((".txt", ".pdf"))
    )
    
    if not files:
        print("[ingest_contracts] No contract files found")
        return {"files": 0, "chunks": 0, "extracted": 0}
    
    print(f"[ingest_contracts] Found {len(files)} contract files")
    
    all_texts = []
    all_metadatas = []
    all_ids = []
    
    # Also store full contract summaries in deal_data for Q&A
    summary_texts = []
    summary_metadatas = []
    summary_ids = []
    
    total_files = 0
    extracted_count = 0
    
    for filename in files:
        filepath = os.path.join(_CONTRACTS_DIR, filename)
        content = read_contract_file(filepath)
        
        if not content:
            print(f"  Skipping: {filename}")
            continue
        
        stem = os.path.splitext(filename)[0]
        print(f"  Processing: {filename}")
        
        # Extract structured metadata if enabled
        extracted = None
        if extract_metadata:
            print(f"    Extracting metadata with Claude...")
            extracted = extract_contract_metadata(content)
            if extracted:
                extracted_count += 1
                print(f"    Extracted: {extracted.get('contract_type', 'unknown')} contract")
        
        # Build base metadata
        if extracted:
            base_meta = {
                "source": filename,
                "doc_type": "contract",
                "contract_type": extracted.get("contract_type", "unknown"),
                "summary": (extracted.get("summary", "")[:500] if extracted.get("summary") else ""),
            }
            
            # Add optional extracted fields
            if extracted.get("effective_date"):
                base_meta["effective_date"] = extracted["effective_date"]
            if extracted.get("end_date"):
                base_meta["end_date"] = extracted["end_date"]
            if extracted.get("total_amount"):
                base_meta["total_amount"] = float(extracted["total_amount"])
            if extracted.get("property_type"):
                base_meta["property_type"] = extracted["property_type"]
            if extracted.get("property_address"):
                base_meta["property_address"] = extracted["property_address"]
            if extracted.get("interest_rate"):
                base_meta["interest_rate"] = float(extracted["interest_rate"])
            
            # Flatten parties
            if extracted.get("parties"):
                party_names = [p.get("name", "") for p in extracted["parties"]]
                party_roles = [f"{p.get('name', '')}:{p.get('role', '')}" for p in extracted["parties"]]
                base_meta["party_names"] = ", ".join(party_names)
                base_meta["party_roles"] = ", ".join(party_roles)
            
            # Create searchable summary for deal_data collection
            total_amt = extracted.get('total_amount')
            total_amt_str = f"${total_amt:,.2f}" if total_amt else "Not specified"
            summary_text = f"""
CONTRACT: {extracted.get('contract_type', 'Unknown')}
SUMMARY: {extracted.get('summary', '')}
SCOPE: {extracted.get('contract_scope', '')}
PARTIES: {base_meta.get('party_roles', '')}
EFFECTIVE DATE: {extracted.get('effective_date', 'Not specified')}
TOTAL AMOUNT: {total_amt_str}
PROPERTY: {extracted.get('property_address', '')} ({extracted.get('property_type', '')})
"""
            if extracted.get("clauses"):
                clause_text = "\n".join(
                    f"- {c.get('clause_type', '')}: {c.get('summary', '')}"
                    for c in extracted["clauses"]
                )
                summary_text += f"\nKEY CLAUSES:\n{clause_text}"
            
            summary_texts.append(summary_text)
            summary_metadatas.append({
                "source": filename,
                "doc_type": "contract_provision",
                "contract_type": extracted.get("contract_type", "unknown"),
            })
            summary_ids.append(f"contract_summary_{stem}")
            
        else:
            # Fallback metadata from filename
            base_meta = {
                "source": filename,
                "doc_type": "contract",
                "contract_type": _infer_type_from_filename(stem),
            }
        
        # Chunk the full contract text for detailed retrieval
        chunks = _splitter.split_text(content)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"contract_{stem}_{i:03d}"
            meta = {
                **base_meta,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            all_texts.append(chunk)
            all_metadatas.append(meta)
            all_ids.append(chunk_id)
        
        total_files += 1
        print(f"    Created {len(chunks)} chunks")
    
    # Ingest chunks into contracts collection
    if all_texts:
        result = add_documents(CONTRACTS_COLLECTION, all_texts, all_metadatas, all_ids)
        print(f"\n[ingest_contracts] Contracts collection: {result['added']} new, "
              f"{result['skipped']} skipped, {result['total']} total")
    
    # Ingest summaries into deal_data collection for Q&A agent
    if summary_texts:
        summary_result = add_documents(
            DEAL_DATA_COLLECTION, summary_texts, summary_metadatas, summary_ids
        )
        print(f"[ingest_contracts] Deal data collection: {summary_result['added']} new summaries")
    
    return {
        "files": total_files,
        "chunks": len(all_texts),
        "extracted": extracted_count,
        "summaries": len(summary_texts),
    }


def _infer_type_from_filename(stem: str) -> str:
    """Infer contract type from filename patterns."""
    stem_lower = stem.lower()
    
    type_keywords = {
        "loan": "Loan Agreement",
        "construction": "Construction Contract",
        "lease": "Lease Agreement",
        "jv": "JV Operating Agreement",
        "joint_venture": "JV Operating Agreement",
        "operating": "JV Operating Agreement",
        "land": "Land Purchase Agreement",
        "purchase": "Land Purchase Agreement",
        "mezzanine": "Mezzanine Financing",
        "mezz": "Mezzanine Financing",
        "preferred": "Preferred Equity Agreement",
        "management": "Property Management Agreement",
        "architect": "Architect Agreement",
        "gc": "General Contractor Agreement",
        "contractor": "General Contractor Agreement",
    }
    
    for keyword, contract_type in type_keywords.items():
        if keyword in stem_lower:
            return contract_type
    
    return "unknown"


def main():
    print("=" * 60)
    print("CONTRACT INGESTION WITH STRUCTURED EXTRACTION")
    print("=" * 60)
    print(f"Source directory: {_CONTRACTS_DIR}")
    print()
    
    result = ingest_contracts(extract_metadata=True)
    
    print()
    print("=" * 60)
    print(f"FILES PROCESSED: {result['files']}")
    print(f"CHUNKS CREATED:  {result['chunks']}")
    print(f"EXTRACTED:       {result['extracted']}")
    print(f"SUMMARIES:       {result.get('summaries', 0)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
