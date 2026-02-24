"""
Combined ingestion runner — runs deal data and market defaults ingestion
in sequence and prints a final status summary.

This is the single command to run after adding new deal files or updating
market defaults. The Streamlit sidebar "Re-index" button calls this.

Usage: python -m FallonPrototype.Financial_Model.shared.run_all_ingestion
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
from FallonPrototype.shared.vector_store import get_collection_counts


def main():
    print("=" * 60)
    print("FALLON FINANCIAL MODEL — FULL DATA INGESTION")
    print("=" * 60)

    print("\n--- Phase 1: Deal Data ---")
    deal_result = ingest_deal_data()

    print("\n--- Phase 2: Market Defaults ---")
    defaults_result = ingest_market_defaults()

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)

    counts = get_collection_counts()
    print(f"  fallon_deal_data:         {counts.get('fallon_deal_data', 0)} chunks "
          f"across {deal_result.get('files', 0)} files")
    print(f"  fallon_market_defaults:   {defaults_result.get('records', 0)} records")
    print("=" * 60)


if __name__ == "__main__":
    main()
