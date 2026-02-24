"""
Combined ingestion runner — runs all data ingestion pipelines in sequence
and prints a final status summary.

This is the single command to run after adding new deal files, updating
market defaults, or adding new contract provision reference docs.
The Streamlit sidebar "Re-index" button calls this.

Usage: python "FallonPrototype/Financial Model/shared/run_all_ingestion.py"
"""

import os
import sys

_FM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROTO_DIR = os.path.dirname(_FM_DIR)

# Add both FallonPrototype parent and Financial Model shared to path
sys.path.insert(0, os.path.dirname(_PROTO_DIR))
sys.path.insert(0, os.path.join(_FM_DIR, "shared"))

from ingest_deal_data import ingest_deal_data
from ingest_market_defaults import ingest_market_defaults
from ingest_contract_provisions import ingest_contract_provisions, ingest_market_research
from FallonPrototype.shared.vector_store import get_collection_counts


def main():
    print("=" * 60)
    print("FALLON FINANCIAL MODEL — FULL DATA INGESTION")
    print("=" * 60)

    print("\n--- Phase 1: Deal Data ---")
    deal_result = ingest_deal_data()

    print("\n--- Phase 2: Market Defaults ---")
    defaults_result = ingest_market_defaults()

    print("\n--- Phase 3: Contract Provisions ---")
    contract_result = ingest_contract_provisions()

    print("\n--- Phase 4: Market Research ---")
    research_result = ingest_market_research()

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)

    counts = get_collection_counts()
    print(f"  fallon_deal_data:            {counts.get('fallon_deal_data', 0)} chunks "
          f"across {deal_result.get('files', 0)} files")
    print(f"  fallon_market_defaults:      {defaults_result.get('records', 0)} records")
    print(f"  fallon_contract_provisions:  {contract_result.get('chunks', 0)} chunks "
          f"across {contract_result.get('files', 0)} files")
    print(f"  fallon_market_research:      {research_result.get('chunks', 0)} chunks "
          f"across {research_result.get('files', 0)} files")
    print("=" * 60)


if __name__ == "__main__":
    main()
