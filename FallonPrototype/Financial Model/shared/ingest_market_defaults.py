"""
Ingest market defaults from JSON into the fallon_market_defaults ChromaDB collection.

Converts each market/program combination into a human-readable text block
and embeds it for semantic retrieval alongside deal comps.

Usage: python -m FallonPrototype.Financial_Model.shared.ingest_market_defaults
"""

import json
import os
import sys

_FM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROTO_DIR = os.path.dirname(_FM_DIR)
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from FallonPrototype.shared.vector_store import add_documents, MARKET_DEFAULTS_COLLECTION

_DEFAULTS_PATH = os.path.join(_FM_DIR, "data", "market_defaults", "market_defaults.json")

# Human-readable labels for variable names
_LABELS = {
    "rent_psf_monthly": "Monthly rent",
    "avg_unit_size_sf": "Avg unit size",
    "stabilized_occupancy_pct": "Stabilized occupancy",
    "annual_rent_growth_pct": "Annual rent growth",
    "lease_up_months": "Lease-up period",
    "other_income_per_unit_monthly": "Other income/unit/mo",
    "rent_psf_annual_nnn": "Office rent (NNN)",
    "free_rent_months": "Free rent concession",
    "ti_allowance_psf": "TI allowance",
    "leasing_commission_pct": "Leasing commission",
    "adr": "Average daily rate",
    "revpar": "RevPAR",
    "total_keys": "Total keys",
    "management_fee_pct": "Management fee",
    "ff_and_e_reserve_pct": "FF&E reserve",
    "hard_cost_psf": "Construction cost",
    "soft_cost_pct_of_hard": "Soft costs (% of hard)",
    "developer_fee_pct_of_total_cost": "Developer fee",
    "contingency_pct_of_hard": "Contingency",
    "carry_cost_months": "Carry period",
    "construction_loan_ltc_pct": "Construction loan LTC",
    "construction_loan_rate_pct": "Construction loan rate",
    "construction_loan_term_months": "Construction loan term",
    "equity_split_lp_pct": "LP equity split",
    "preferred_return_pct": "LP preferred return",
    "promote_pct": "GP promote",
    "exit_cap_rate_pct": "Exit cap rate",
    "exit_sale_cost_pct": "Disposition costs",
    "exit_year": "Hold period",
}


def _format_value(entry: dict) -> str:
    """Format a single variable entry as a human-readable string."""
    val = entry.get("value")
    unit = entry.get("unit", "")
    if val is None:
        return "not available"
    if "%" in unit:
        return f"{val}%"
    if "$/sf/month" in unit:
        return f"${val}/sf/month"
    if "$/sf/year" in unit:
        return f"${val}/sf/year"
    if "$/sf" in unit:
        return f"${val}/sf"
    if "$/night" in unit:
        return f"${val}/night"
    if "$/unit/month" in unit:
        return f"${val}/unit/month"
    if "$/available room" in unit:
        return f"${val}/room/night"
    if unit == "months":
        return f"{val} months"
    if unit == "years":
        return f"{val} years"
    if unit == "sf":
        return f"{val} sf"
    if unit == "keys":
        return f"{val} keys"
    return str(val)


def _build_text_block(market: str, program_type: str, data: dict, meta: dict) -> str:
    """Convert a market/program defaults dict into a human-readable text block."""
    quality = meta.get("data_quality", "estimated")
    updated = meta.get("last_updated", "unknown")

    lines = [
        f"{market.replace('_', ' ').title()} {program_type} development assumptions "
        f"({updated}, data quality: {quality}):"
    ]

    parts = []
    for var_name, entry in data.items():
        if not isinstance(entry, dict) or "value" not in entry:
            continue
        label = _LABELS.get(var_name, var_name.replace("_", " ").title())
        formatted = _format_value(entry)
        source = entry.get("source", "")
        parts.append(f"{label}: {formatted}")

    lines.append(" | ".join(parts))

    # Add primary source
    first_source = ""
    for entry in data.values():
        if isinstance(entry, dict) and entry.get("source"):
            first_source = entry["source"]
            break
    if first_source:
        lines.append(f"Source: {first_source}")

    return "\n".join(lines)


def ingest_market_defaults() -> dict:
    """Ingest market defaults JSON into the vector store as text records."""
    if not os.path.exists(_DEFAULTS_PATH):
        print(f"[ingest_market_defaults] File not found: {_DEFAULTS_PATH}")
        return {"records": 0}

    with open(_DEFAULTS_PATH, "r") as f:
        defaults = json.load(f)

    all_texts = []
    all_metadatas = []
    all_ids = []

    for market, market_data in defaults.items():
        meta = market_data.get("_meta", {})

        for program_type, program_data in market_data.items():
            if program_type == "_meta":
                continue
            if not isinstance(program_data, dict):
                continue

            text = _build_text_block(market, program_type, program_data, meta)
            doc_id = f"defaults_{market}_{program_type}"
            metadata = {
                "market": market,
                "program_type": program_type,
                "data_quality": meta.get("data_quality", "estimated"),
                "last_updated": meta.get("last_updated", "unknown"),
            }

            all_texts.append(text)
            all_metadatas.append(metadata)
            all_ids.append(doc_id)
            print(f"  {market}/{program_type}: {len(text)} chars")

    if all_texts:
        result = add_documents(
            MARKET_DEFAULTS_COLLECTION, all_texts, all_metadatas, all_ids
        )
        print(f"\n[ingest_market_defaults] Done: {len(all_texts)} records, "
              f"{result['added']} new, {result['skipped']} skipped, "
              f"{result['total']} total in collection")
    else:
        result = {"added": 0, "total": 0}

    return {"records": len(all_texts)}


def main():
    print("=" * 60)
    print("MARKET DEFAULTS INGESTION")
    print("=" * 60)
    ingest_market_defaults()
    print("=" * 60)


if __name__ == "__main__":
    main()
