"""
Combined ingestion runner — runs all data ingestion pipelines in sequence.

Usage: python -m FallonPrototype.shared.run_all_ingestion
"""

import os
import sys

_SHARED_DIR = os.path.dirname(os.path.abspath(__file__))
_PROTO_DIR = os.path.dirname(_SHARED_DIR)
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from FallonPrototype.shared.ingest_deal_data import ingest_deal_data
from FallonPrototype.shared.ingest_market_defaults import ingest_market_defaults
from FallonPrototype.shared.vector_store import get_collection_counts


def main():
    print("=" * 60)
    print("FALLON FINANCIAL MODEL - FULL DATA INGESTION")
    print("=" * 60)

    print("\n--- Phase 1: Deal Data ---")
    deal_result = ingest_deal_data()

    print("\n--- Phase 2: Market Defaults ---")
    defaults_result = ingest_market_defaults()

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)

    counts = get_collection_counts()
    print(f"  fallon_deal_data:       {counts.get('fallon_deal_data', 0)} chunks")
    print(f"  fallon_market_defaults: {counts.get('fallon_market_defaults', 0)} records")
    print("=" * 60)


if __name__ == "__main__":
    main()
