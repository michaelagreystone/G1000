"""
Financial Model Agent — Parameter Extractor (Phase 2)

Converts plain-English project descriptions into structured ProjectParameters,
validates required fields, and handles clarification flows for missing data.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

import sys
import os
_PROTO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from FallonPrototype.shared.claude_client import call_claude


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2.1 — Schema Definition
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProjectParameters:
    """
    Structured representation of a real estate development project.
    
    Field Categories:
    - Hard required: market, program_type (generation fails without these)
    - Soft required: unit_count/rentable_sf, land_cost/acreage (defaults used if missing)
    - Optional: return targets, timing, mixed-use components (pure defaults, labeled "estimated")
    """
    # Required — model cannot generate without these
    market: Optional[str] = None              # "charlotte" | "nashville" | "boston" | "other"
    program_type: Optional[str] = None        # "multifamily" | "office" | "hotel" | "mixed_use" | "condo"

    # Dimensional inputs — used to calculate revenue and costs
    unit_count: Optional[int] = None          # residential units
    rentable_sf: Optional[int] = None         # office/retail square footage
    total_gfa_sf: Optional[int] = None        # gross floor area (all uses)
    land_cost: Optional[float] = None         # total land cost in dollars
    acreage: Optional[float] = None           # site size

    # Return targets — user's goals for the deal
    target_lp_irr_pct: Optional[float] = None
    target_equity_multiple: Optional[float] = None

    # Timing
    construction_start: Optional[str] = None          # free text: "Q3 2026", "next year"
    construction_duration_months: Optional[int] = None

    # Program mix (for mixed_use)
    mixed_use_components: list[str] = field(default_factory=list)
                                              # e.g. ["multifamily", "retail", "hotel"]

    # Hotel-specific
    total_keys: Optional[int] = None          # hotel room count

    # Any additional context from the query that doesn't fit above
    notes: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2.2 — Claude-Powered Extraction
# ═══════════════════════════════════════════════════════════════════════════════

EXTRACTION_SYSTEM_PROMPT = """You are a real estate financial analyst assistant. Extract project parameters from the user's description and return ONLY a valid JSON object with the following fields. Use null for any field not mentioned. Do not add explanation, commentary, or markdown formatting — return only the raw JSON object.

Required fields:
{
  "market": string or null,
  "program_type": string or null,
  "unit_count": integer or null,
  "rentable_sf": integer or null,
  "total_gfa_sf": integer or null,
  "land_cost": float or null,
  "acreage": float or null,
  "target_lp_irr_pct": float or null,
  "target_equity_multiple": float or null,
  "construction_start": string or null,
  "construction_duration_months": integer or null,
  "mixed_use_components": array of strings or [],
  "total_keys": integer or null,
  "notes": string (capture any project context not in the above fields)
}

Normalize these values:
- market must be one of: "charlotte", "nashville", "boston", "other"
- program_type must be one of: "multifamily", "office", "hotel", "mixed_use", "condo"
- All percentages as floats 0–100 (14% → 14.0, not 0.14)
- unit_count, rentable_sf, total_gfa_sf, and total_keys as integers, not strings
- For mixed_use projects, populate mixed_use_components with the component types

Examples:
- "200 units in Charlotte" → {"market": "charlotte", "program_type": "multifamily", "unit_count": 200, ...}
- "80k sf office in Boston" → {"market": "boston", "program_type": "office", "rentable_sf": 80000, ...}
- "hotel and apartments in Nashville, 300 keys" → {"market": "nashville", "program_type": "mixed_use", "mixed_use_components": ["hotel", "multifamily"], "total_keys": 300, ...}

Return ONLY the JSON object."""


def extract_parameters(query: str) -> ProjectParameters:
    """
    Extract project parameters from a plain-English query using Claude.
    
    Args:
        query: User's natural language project description.
    
    Returns:
        ProjectParameters dataclass with extracted values. Fields not mentioned
        in the query will be None.
    """
    response = call_claude(EXTRACTION_SYSTEM_PROMPT, query, max_tokens=512)
    
    if response.startswith("ERROR:"):
        return ProjectParameters(notes=f"Extraction failed: {response}")
    
    # Strip markdown fences if present
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    
    # Find JSON object boundaries
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return ProjectParameters(notes=f"Could not parse JSON from response: {response[:200]}")
    
    json_str = cleaned[start:end + 1]
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return ProjectParameters(notes=f"JSON parse error: {e}. Response: {response[:200]}")
    
    # Hydrate dataclass
    return ProjectParameters(
        market=data.get("market"),
        program_type=data.get("program_type"),
        unit_count=data.get("unit_count"),
        rentable_sf=data.get("rentable_sf"),
        total_gfa_sf=data.get("total_gfa_sf"),
        land_cost=data.get("land_cost"),
        acreage=data.get("acreage"),
        target_lp_irr_pct=data.get("target_lp_irr_pct"),
        target_equity_multiple=data.get("target_equity_multiple"),
        construction_start=data.get("construction_start"),
        construction_duration_months=data.get("construction_duration_months"),
        mixed_use_components=data.get("mixed_use_components") or [],
        total_keys=data.get("total_keys"),
        notes=data.get("notes") or "",
    )


def normalize_parameters(params: ProjectParameters) -> ProjectParameters:
    """
    Apply light corrections after extraction to standardize values.
    
    Normalizations:
    - Lowercase and strip whitespace from market and program_type
    - Map common synonyms to canonical values
    - Estimate total_gfa_sf from unit_count if not provided
    """
    # Normalize market
    if params.market:
        market = params.market.lower().strip()
        # Map variations
        market_map = {
            "charlotte, nc": "charlotte",
            "charlotte nc": "charlotte",
            "clt": "charlotte",
            "nashville, tn": "nashville",
            "nashville tn": "nashville",
            "boston, ma": "boston",
            "boston ma": "boston",
            "seaport": "boston",
            "south end": "charlotte",
        }
        params.market = market_map.get(market, market)
        if params.market not in ("charlotte", "nashville", "boston", "other"):
            params.market = "other"
    
    # Normalize program_type
    if params.program_type:
        prog = params.program_type.lower().strip().replace("-", "_").replace(" ", "_")
        prog_map = {
            "apartment": "multifamily",
            "apartments": "multifamily",
            "residential": "multifamily",
            "multi_family": "multifamily",
            "commercial": "office",
            "class_a_office": "office",
            "hospitality": "hotel",
            "condos": "condo",
            "condominium": "condo",
            "mixed": "mixed_use",
        }
        params.program_type = prog_map.get(prog, prog)
    
    # Estimate total_gfa_sf from unit_count if not provided (avg 900sf/unit)
    if params.unit_count and not params.total_gfa_sf:
        params.total_gfa_sf = params.unit_count * 900
    
    # For office, use rentable_sf as total_gfa_sf if not provided
    if params.rentable_sf and not params.total_gfa_sf and params.program_type == "office":
        params.total_gfa_sf = int(params.rentable_sf * 1.15)  # ~15% common area factor
    
    return params


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2.3 — Missing Parameter Handler
# ═══════════════════════════════════════════════════════════════════════════════

def check_missing_parameters(params: ProjectParameters) -> list[str]:
    """
    Check for missing required parameters.
    
    Returns:
        List of human-readable descriptions of missing fields.
        Empty list means all required fields are present.
    """
    missing = []
    
    # Hard required — generation fails without these
    if not params.market:
        missing.append("market (Charlotte, Nashville, Boston, or other)")
    
    if not params.program_type:
        missing.append("program type (multifamily, office, hotel, condo, or mixed-use)")
    
    # Soft required — at least one dimensional input needed
    has_dimension = (
        params.unit_count is not None or
        params.rentable_sf is not None or
        params.total_gfa_sf is not None or
        params.total_keys is not None
    )
    if not has_dimension:
        if params.program_type == "multifamily" or params.program_type == "condo":
            missing.append("unit count (number of residential units)")
        elif params.program_type == "office":
            missing.append("rentable square footage")
        elif params.program_type == "hotel":
            missing.append("total keys (number of hotel rooms)")
        else:
            missing.append("project size (unit count, square footage, or hotel keys)")
    
    return missing


def format_clarification_message(missing: list[str]) -> str:
    """
    Format a specific, actionable clarification message for missing fields.
    
    Args:
        missing: List of missing field descriptions from check_missing_parameters().
    
    Returns:
        User-friendly message asking for the specific missing information.
    """
    if not missing:
        return ""
    
    if len(missing) == 1:
        return f"To generate your pro forma, I need one more detail:\n• {missing[0]}\n\nReply with that information and I'll build the model."
    
    items = "\n".join(f"• {m}" for m in missing)
    return f"To generate your pro forma, I need a few more details:\n{items}\n\nReply with those details and I'll build the model."


def merge_clarification(original_params: ProjectParameters, clarification_text: str) -> ProjectParameters:
    """
    Merge clarification response with original parameters.
    
    Re-runs extraction on the clarification text and copies any non-null
    fields into the original params, overwriting only null fields.
    
    Args:
        original_params: The parameters from the first extraction pass.
        clarification_text: User's response to the clarification prompt.
    
    Returns:
        Merged ProjectParameters with gaps filled from clarification.
    """
    clarification_params = normalize_parameters(extract_parameters(clarification_text))
    
    # Copy non-null fields from clarification into original
    if clarification_params.market and not original_params.market:
        original_params.market = clarification_params.market
    if clarification_params.program_type and not original_params.program_type:
        original_params.program_type = clarification_params.program_type
    if clarification_params.unit_count and not original_params.unit_count:
        original_params.unit_count = clarification_params.unit_count
    if clarification_params.rentable_sf and not original_params.rentable_sf:
        original_params.rentable_sf = clarification_params.rentable_sf
    if clarification_params.total_gfa_sf and not original_params.total_gfa_sf:
        original_params.total_gfa_sf = clarification_params.total_gfa_sf
    if clarification_params.land_cost and not original_params.land_cost:
        original_params.land_cost = clarification_params.land_cost
    if clarification_params.acreage and not original_params.acreage:
        original_params.acreage = clarification_params.acreage
    if clarification_params.target_lp_irr_pct and not original_params.target_lp_irr_pct:
        original_params.target_lp_irr_pct = clarification_params.target_lp_irr_pct
    if clarification_params.target_equity_multiple and not original_params.target_equity_multiple:
        original_params.target_equity_multiple = clarification_params.target_equity_multiple
    if clarification_params.construction_start and not original_params.construction_start:
        original_params.construction_start = clarification_params.construction_start
    if clarification_params.construction_duration_months and not original_params.construction_duration_months:
        original_params.construction_duration_months = clarification_params.construction_duration_months
    if clarification_params.mixed_use_components and not original_params.mixed_use_components:
        original_params.mixed_use_components = clarification_params.mixed_use_components
    if clarification_params.total_keys and not original_params.total_keys:
        original_params.total_keys = clarification_params.total_keys
    if clarification_params.notes and not original_params.notes:
        original_params.notes = clarification_params.notes
    
    # Re-normalize after merge
    return normalize_parameters(original_params)


def params_to_dict(params: ProjectParameters) -> dict:
    """Convert ProjectParameters to a plain dict for JSON serialization."""
    return asdict(params)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3 — Context Retriever
# ═══════════════════════════════════════════════════════════════════════════════

from FallonPrototype.shared.vector_store import (
    query_collection,
    get_market_defaults,
    DEAL_DATA_COLLECTION,
    MARKET_DEFAULTS_COLLECTION,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3.1 — Deal Comps Retrieval
# ═══════════════════════════════════════════════════════════════════════════════

def build_deal_query(params: ProjectParameters) -> str:
    """
    Construct a targeted retrieval query from project parameters.
    
    Builds a query string optimized for surfacing financial content
    (pro forma, returns, assumptions) rather than narrative description.
    
    Args:
        params: Extracted project parameters.
    
    Returns:
        Query string biased toward financial content retrieval.
    """
    parts = []
    
    if params.market:
        parts.append(params.market.title())
    
    if params.program_type:
        prog = params.program_type.replace("_", " ")
        if params.program_type == "multifamily":
            parts.append("multifamily residential")
        elif params.program_type == "mixed_use":
            components = params.mixed_use_components or ["hotel", "residential"]
            parts.append("mixed-use development")
            parts.append(" ".join(components))
        elif params.program_type == "office":
            parts.append("Class A office")
        elif params.program_type == "hotel":
            parts.append("hotel hospitality")
        else:
            parts.append(prog)
    
    parts.append("development pro forma IRR returns assumptions")
    
    return " ".join(parts)


def retrieve_deal_comps(params: ProjectParameters) -> list[dict]:
    """
    Retrieve comparable deal memos from the vector store.
    
    Two-pass approach:
    1. Semantic search for relevance
    2. Metadata-filtered search for market specificity
    Results are merged, deduplicated, and filtered to top 4 by distance.
    
    Args:
        params: Extracted project parameters.
    
    Returns:
        List of deal comp chunks (up to 4), sorted by relevance.
        Empty list if corpus is empty or no relevant comps found.
    """
    query = build_deal_query(params)
    
    # Pass 1: Semantic search (broad relevance)
    semantic_results = query_collection(
        DEAL_DATA_COLLECTION,
        query,
        n_results=4,
    )
    
    # Pass 2: Metadata-filtered search (market-specific)
    market_results = []
    if params.market:
        market_results = query_collection(
            DEAL_DATA_COLLECTION,
            query,
            n_results=2,
            where={"market": {"$eq": params.market.lower()}},
        )
    
    # Merge and deduplicate by chunk text (most reliable dedup key)
    seen_texts = set()
    merged = []
    
    for result in market_results + semantic_results:
        chunk_text = result.get("text", "")[:200]  # Use first 200 chars as dedup key
        if chunk_text not in seen_texts:
            seen_texts.add(chunk_text)
            merged.append(result)
    
    # Sort by distance (lower = more similar) and take top 4
    merged.sort(key=lambda r: r["distance"])
    top_results = merged[:4]
    
    # Filter out low-relevance chunks (they add noise)
    filtered = [r for r in top_results if r["relevance"] != "low"]
    
    return filtered


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3.2 — Market Defaults Retrieval
# ═══════════════════════════════════════════════════════════════════════════════

def get_defaults_for_params(params: ProjectParameters) -> dict | None:
    """
    Direct lookup of market defaults for the given parameters.
    
    Handles mixed_use by retrieving and merging defaults for each component.
    
    Args:
        params: Extracted project parameters.
    
    Returns:
        Dict of market defaults, or None if market/program not found.
        For mixed_use, returns a dict with each component's defaults labeled.
    """
    if not params.market or not params.program_type:
        return None
    
    # Standard single-program lookup
    if params.program_type != "mixed_use":
        return get_market_defaults(params.market, params.program_type)
    
    # Mixed-use: retrieve defaults for each component
    components = params.mixed_use_components or ["multifamily", "retail"]
    combined = {"_mixed_use": True, "_components": {}}
    any_fallback = False
    
    for component in components:
        component_defaults = get_market_defaults(params.market, component)
        if component_defaults:
            combined["_components"][component] = component_defaults
            if component_defaults.get("_fallback"):
                any_fallback = True
    
    if not combined["_components"]:
        return None
    
    if any_fallback:
        combined["_fallback"] = True
        combined["_fallback_reason"] = f"One or more components using national averages for market '{params.market}'."
    
    return combined


def retrieve_defaults_context(params: ProjectParameters) -> list[dict]:
    """
    Retrieve market defaults context from vector store for Claude reasoning.
    
    Uses metadata filtering to ensure only the correct market's defaults
    are returned.
    
    Args:
        params: Extracted project parameters.
    
    Returns:
        List of defaults context chunks from vector store.
    """
    if not params.market:
        return []
    
    query = f"{params.market} {params.program_type or 'development'} market assumptions defaults rent cost cap rate"
    
    results = query_collection(
        MARKET_DEFAULTS_COLLECTION,
        query,
        n_results=3,
        where={"market": {"$eq": params.market.lower()}},
    )
    
    return results


def get_fallback_warning(defaults: dict | None, market: str) -> str | None:
    """
    Generate a warning string if defaults are using national fallback.
    
    Args:
        defaults: The defaults dict from get_defaults_for_params().
        market: The requested market name.
    
    Returns:
        Warning string if fallback is in use, None otherwise.
    """
    if not defaults:
        return None
    
    if defaults.get("_fallback"):
        return (
            f"WARNING: No market-specific defaults available for '{market}'. "
            "National averages used. All cost and revenue assumptions require "
            "local broker verification before use."
        )
    
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3.3 — Context Formatter
# ═══════════════════════════════════════════════════════════════════════════════

def _format_deal_comp(comp: dict, index: int) -> str:
    """Format a single deal comp chunk for the context block."""
    source = comp["metadata"].get("source", "unknown")
    relevance = comp.get("relevance", "unknown")
    text = comp.get("text", "")
    
    return f"""--- COMPARABLE {index} ---
Source: {source} | Relevance: {relevance}
{text}
"""


def _format_defaults_section(defaults: dict | None, params: ProjectParameters) -> str:
    """Format the structured defaults section."""
    if not defaults:
        return """═══════════════════════════════════════════
SECTION 2: CURRENT MARKET DEFAULTS
═══════════════════════════════════════════
No market defaults available. Using estimation based on comparable markets.
"""
    
    # Handle mixed-use differently
    if defaults.get("_mixed_use"):
        lines = [
            "═══════════════════════════════════════════",
            "SECTION 2: CURRENT MARKET DEFAULTS (MIXED-USE)",
            f"Market: {params.market.title() if params.market else 'Unknown'} | Program: Mixed-Use",
            "═══════════════════════════════════════════",
            "",
        ]
        
        for component, component_defaults in defaults.get("_components", {}).items():
            lines.append(f"--- {component.upper()} COMPONENT ---")
            lines.extend(_format_defaults_items(component_defaults))
            lines.append("")
        
        return "\n".join(lines)
    
    # Standard single-program defaults
    meta = defaults.get("_meta", {}) if isinstance(defaults.get("_meta"), dict) else {}
    data_quality = meta.get("data_quality", defaults.get("data_quality", "estimated"))
    last_updated = meta.get("last_updated", defaults.get("last_updated", "unknown"))
    
    lines = [
        "═══════════════════════════════════════════",
        "SECTION 2: CURRENT MARKET DEFAULTS",
        f"Market: {params.market.title() if params.market else 'Unknown'} | "
        f"Program: {params.program_type.replace('_', ' ').title() if params.program_type else 'Unknown'} | "
        f"Data Quality: {data_quality}",
        f"Last Updated: {last_updated}",
        "═══════════════════════════════════════════",
        "",
    ]
    
    lines.extend(_format_defaults_items(defaults))
    
    return "\n".join(lines)


def _format_defaults_items(defaults: dict) -> list[str]:
    """Format individual defaults items into lines."""
    lines = []
    
    for key, val in defaults.items():
        if key.startswith("_"):
            continue
        
        if isinstance(val, dict) and "value" in val:
            value = val["value"]
            unit = val.get("unit", "")
            source = val.get("source", "")
            label = key.replace("_", " ").replace("pct", "%").replace("psf", "/sf")
            lines.append(f"{label:30} {value} {unit:20} (Source: {source[:50]})")
        elif not isinstance(val, dict):
            lines.append(f"{key:30} {val}")
    
    return lines


def format_financial_context(
    deal_comps: list[dict],
    defaults_dict: dict | None,
    defaults_chunks: list[dict],
    params: ProjectParameters,
) -> str:
    """
    Assemble the complete context block for Claude.
    
    Produces a structured, labeled context with three sections:
    1. Historical Fallon deal comparables
    2. Current market defaults (structured)
    3. Retrieved defaults context (for reasoning)
    
    Args:
        deal_comps: List of deal comp chunks from retrieve_deal_comps().
        defaults_dict: Structured defaults from get_defaults_for_params().
        defaults_chunks: Vector-retrieved defaults from retrieve_defaults_context().
        params: The project parameters for labeling.
    
    Returns:
        Formatted context string for Claude prompt injection.
    """
    sections = []
    
    # Section 1: Deal Comparables
    sections.append("═══════════════════════════════════════════")
    sections.append("SECTION 1: HISTORICAL FALLON DEAL COMPARABLES")
    sections.append("═══════════════════════════════════════════")
    sections.append("")
    
    if deal_comps:
        for i, comp in enumerate(deal_comps, 1):
            sections.append(_format_deal_comp(comp, i))
    else:
        sections.append("No historical Fallon comps available for this market/program.")
        sections.append("Using market defaults only.")
    sections.append("")
    
    # Section 2: Structured Defaults
    sections.append(_format_defaults_section(defaults_dict, params))
    sections.append("")
    
    # Section 3: Retrieved Defaults Context
    sections.append("═══════════════════════════════════════════")
    sections.append("SECTION 3: RETRIEVED DEFAULTS CONTEXT")
    sections.append("═══════════════════════════════════════════")
    sections.append("")
    
    if defaults_chunks:
        for chunk in defaults_chunks:
            source = chunk["metadata"].get("source", "unknown")
            sections.append(f"[{source}]")
            sections.append(chunk.get("text", ""))
            sections.append("")
    else:
        sections.append("No additional defaults context retrieved.")
    sections.append("")
    
    # Context quality summary line
    high_count = sum(1 for c in deal_comps if c.get("relevance") == "high")
    medium_count = sum(1 for c in deal_comps if c.get("relevance") == "medium")
    
    comp_summary = f"{len(deal_comps)} deal comps"
    if deal_comps:
        comp_summary += f" ({high_count} high, {medium_count} medium relevance)"
    
    defaults_summary = "None"
    if defaults_dict:
        market = params.market.title() if params.market else "Unknown"
        program = params.program_type.replace("_", " ") if params.program_type else "unknown"
        fallback = "Yes" if defaults_dict.get("_fallback") else "No"
        defaults_summary = f"{market} {program} | Fallback: {fallback}"
    
    sections.append("───────────────────────────────────────────")
    sections.append(f"Context quality: {comp_summary} | Market defaults: {defaults_summary}")
    sections.append("───────────────────────────────────────────")
    
    return "\n".join(sections)


def assemble_context(params: ProjectParameters) -> tuple[str, str | None]:
    """
    Main entry point for Phase 3 — assemble complete context for pro forma generation.
    
    Retrieves deal comps, market defaults, and formats everything into a
    single context block ready for Claude.
    
    Args:
        params: Extracted and validated project parameters.
    
    Returns:
        Tuple of (formatted_context, fallback_warning).
        fallback_warning is None if market-specific defaults were found.
    """
    # Retrieve deal comparables
    deal_comps = retrieve_deal_comps(params)
    
    # Retrieve market defaults (structured + vector)
    defaults_dict = get_defaults_for_params(params)
    defaults_chunks = retrieve_defaults_context(params)
    
    # Check for fallback warning
    fallback_warning = get_fallback_warning(defaults_dict, params.market or "unknown")
    
    # Format everything into a single context block
    context = format_financial_context(
        deal_comps,
        defaults_dict,
        defaults_chunks,
        params,
    )
    
    return context, fallback_warning


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4 — Pro Forma Generator
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4.1 — Pro Forma Output Schema
# ═══════════════════════════════════════════════════════════════════════════════

PRO_FORMA_SCHEMA = {
    "project_summary": {
        "deal_name": {"type": "str"},
        "market": {"type": "str"},
        "program_type": {"type": "str"},
        "total_gfa_sf": {"type": "value_field"},
        "unit_count": {"type": "value_field", "nullable": True},
        "rentable_sf": {"type": "value_field", "nullable": True},
        "construction_start": {"type": "value_field"},
        "construction_duration_months": {"type": "value_field"},
        "total_keys": {"type": "value_field", "nullable": True},
        "notes": {"type": "str"},
    },
    "revenue_assumptions": {
        "rent_psf_monthly": {"type": "value_field", "nullable": True},
        "rent_psf_annual_nnn": {"type": "value_field", "nullable": True},
        "adr": {"type": "value_field", "nullable": True},
        "stabilized_occupancy_pct": {"type": "value_field"},
        "lease_up_months": {"type": "value_field"},
        "annual_rent_growth_pct": {"type": "value_field"},
        "other_income_per_unit_monthly": {"type": "value_field", "nullable": True},
    },
    "cost_assumptions": {
        "land_cost_total": {"type": "value_field"},
        "hard_cost_psf": {"type": "value_field"},
        "hard_cost_total": {"type": "value_field"},
        "soft_cost_pct_of_hard": {"type": "value_field"},
        "soft_cost_total": {"type": "value_field"},
        "developer_fee_pct": {"type": "value_field"},
        "developer_fee_total": {"type": "value_field"},
        "contingency_pct": {"type": "value_field"},
        "contingency_total": {"type": "value_field"},
        "total_project_cost": {"type": "value_field"},
    },
    "financing_assumptions": {
        "construction_loan_ltc_pct": {"type": "value_field"},
        "construction_loan_amount": {"type": "value_field"},
        "construction_loan_rate_pct": {"type": "value_field"},
        "carry_cost_total": {"type": "value_field"},
        "equity_required": {"type": "value_field"},
        "lp_equity_pct": {"type": "value_field"},
        "lp_equity_amount": {"type": "value_field"},
        "gp_equity_pct": {"type": "value_field"},
        "gp_equity_amount": {"type": "value_field"},
    },
    "return_metrics": {
        "exit_cap_rate_pct": {"type": "value_field"},
        "exit_year": {"type": "value_field"},
        "stabilized_noi": {"type": "value_field"},
        "gross_exit_value": {"type": "value_field"},
        "net_exit_value": {"type": "value_field"},
        "total_profit": {"type": "value_field"},
        "profit_on_cost_pct": {"type": "value_field"},
        "development_spread_bps": {"type": "value_field"},
        "project_irr_levered_pct": {"type": "value_field"},
        "equity_multiple_lp": {"type": "value_field"},
        "lp_irr_pct": {"type": "value_field"},
    },
}

VALID_LABELS = {"confirmed", "estimated", "calculated", "missing"}


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4.2 — System Prompt Engineering
# ═══════════════════════════════════════════════════════════════════════════════

GENERATION_SYSTEM_PROMPT = """You are a real estate financial analyst for The Fallon Company, a merchant developer based in Boston with a $6B development pipeline. Your task is to generate a complete development pro forma in JSON format based on the project parameters and market context provided.

CRITICAL RULES:

1. GROUNDING: Use ONLY the values provided in the market defaults and historical deal comparables sections of the context. Do not use general knowledge or external benchmarks. If a value is not in the context and cannot be calculated from values that are, set "value" to null and "label" to "missing".

2. LABEL TAXONOMY: Every numeric value must have a "label" field set to exactly one of:
   - "confirmed": value was explicitly stated by the user
   - "estimated": value sourced from the provided market defaults
   - "calculated": value derived mathematically from other values in this model
   - "missing": value is required but not available in context or user input

3. VALUE STRUCTURE: Every numeric field must be a dict with exactly these keys:
   {
     "value": <number or null>,
     "unit": "<unit string>",
     "label": "<one of: confirmed, estimated, calculated, missing>",
     "source": "<source string, formula, or 'user-provided'>"
   }

4. OUTPUT FORMAT: Return ONLY the JSON object. No explanation before or after. No markdown code fences. No commentary. The entire response must be valid JSON that can be parsed by json.loads() without modification.

5. RETURN METRICS: For "project_irr_levered_pct" and "equity_multiple_lp", use the provided market defaults as baselines. If the assumptions imply returns significantly above or below market norms, note this in the project_summary.notes field.

6. REQUIRED SECTIONS: Your output must have exactly these five top-level keys:
   - project_summary
   - revenue_assumptions
   - cost_assumptions
   - financing_assumptions
   - return_metrics

7. CALCULATIONS: For fields marked as "calculated", show the formula in the source field. Examples:
   - "source": "hard_cost_psf * total_gfa_sf"
   - "source": "noi / exit_cap_rate"
   - "source": "total_project_cost - construction_loan_amount"

8. DEAL NAME: Generate a descriptive deal name in the format "[Market] [Program Type] [Size]", e.g., "Charlotte Multifamily 200 Units" or "Nashville Mixed-Use 150K SF".
"""


def build_generation_message(params: ProjectParameters, context: str) -> str:
    """
    Build the user message for pro forma generation.
    
    Args:
        params: Extracted project parameters.
        context: Formatted context from Phase 3.
    
    Returns:
        Complete user message for Claude.
    """
    def fmt(val, default="not specified"):
        if val is None:
            return default
        if isinstance(val, float):
            return f"${val:,.0f}" if val > 1000 else str(val)
        return str(val)
    
    message = f"""PROJECT PARAMETERS:
Market: {fmt(params.market)}
Program type: {fmt(params.program_type)}
Unit count: {fmt(params.unit_count)}
Rentable SF: {fmt(params.rentable_sf)}
Total GFA: {fmt(params.total_gfa_sf)}
Land cost: {fmt(params.land_cost)}
Target LP IRR: {fmt(params.target_lp_irr_pct, "use market default")}%
Target equity multiple: {fmt(params.target_equity_multiple, "use market default")}x
Construction start: {fmt(params.construction_start)}
Construction duration: {fmt(params.construction_duration_months)} months
Hotel keys: {fmt(params.total_keys)}
Mixed-use components: {', '.join(params.mixed_use_components) if params.mixed_use_components else 'N/A'}
Additional notes: {params.notes or 'none'}

CONTEXT:
{context}

Generate the complete pro forma JSON for this project."""
    
    return message


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4.3 — JSON Parsing & Validation
# ═══════════════════════════════════════════════════════════════════════════════

def extract_json_from_response(response: str) -> dict | None:
    """
    Extract and parse JSON from Claude's response.
    
    Handles markdown fences, leading/trailing text, and other common
    response format issues.
    
    Args:
        response: Raw response string from Claude.
    
    Returns:
        Parsed dict on success, None on failure.
    """
    if not response:
        return None
    
    cleaned = response.strip()
    
    # Strip markdown fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    
    # Find JSON boundaries
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    
    if start == -1 or end == -1 or end <= start:
        _log_parse_failure(response, "No valid JSON boundaries found")
        return None
    
    json_str = cleaned[start:end + 1]
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        _log_parse_failure(response, f"JSON decode error: {e}")
        return None


def _log_parse_failure(response: str, error: str) -> None:
    """Log parse failures for debugging."""
    log_dir = os.path.join(_PROTO_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "parse_failures.jsonl")
    
    import datetime
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "error": error,
        "response_preview": response[:500] if response else None,
    }
    
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def validate_pro_forma(data: dict) -> tuple[bool, list[str]]:
    """
    Validate a parsed pro forma against the schema.
    
    Args:
        data: Parsed pro forma dict.
    
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required top-level sections
    required_sections = ["project_summary", "revenue_assumptions", "cost_assumptions",
                         "financing_assumptions", "return_metrics"]
    
    for section in required_sections:
        if section not in data:
            errors.append(f"Missing required section: {section}")
    
    if errors:
        return False, errors
    
    # Check value fields have required structure
    for section_name, section_schema in PRO_FORMA_SCHEMA.items():
        section_data = data.get(section_name, {})
        
        for field_name, field_schema in section_schema.items():
            field_data = section_data.get(field_name)
            
            if field_schema.get("type") == "value_field":
                if field_data is None:
                    if not field_schema.get("nullable"):
                        errors.append(f"{section_name}.{field_name}: missing field")
                    continue
                
                if not isinstance(field_data, dict):
                    errors.append(f"{section_name}.{field_name}: expected dict, got {type(field_data).__name__}")
                    continue
                
                # Check required keys
                for key in ["value", "unit", "label", "source"]:
                    if key not in field_data:
                        errors.append(f"{section_name}.{field_name}: missing '{key}' key")
                
                # Check label is valid
                if "label" in field_data and field_data["label"] not in VALID_LABELS:
                    errors.append(f"{section_name}.{field_name}: invalid label '{field_data['label']}'")
    
    # Critical check: total_project_cost must be present and numeric
    tpc = data.get("cost_assumptions", {}).get("total_project_cost", {})
    if not isinstance(tpc, dict) or tpc.get("value") is None:
        errors.append("cost_assumptions.total_project_cost must have a numeric value")
    
    return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4.4 — Return Metrics Calculator (imported from separate module)
# ═══════════════════════════════════════════════════════════════════════════════

# Calculator functions are in FallonPrototype/shared/return_calculator.py


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4.6 — Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgentResponse:
    """Structured response from the financial agent."""
    intent: str
    answer: str
    sources: list[str]
    raw_chunks: list[dict]
    confidence: str  # "high" | "medium" | "low"
    export_data: dict | None = None
    needs_clarification: bool = False
    warnings: list[str] = field(default_factory=list)


def generate_pro_forma(params: ProjectParameters, context: str) -> dict | None:
    """
    Generate a pro forma using Claude.
    
    Args:
        params: Validated project parameters.
        context: Formatted context from Phase 3.
    
    Returns:
        Parsed pro forma dict, or None if generation fails after retry.
    """
    message = build_generation_message(params, context)
    
    # First attempt
    raw_response = call_claude(GENERATION_SYSTEM_PROMPT, message, max_tokens=4096)
    
    if raw_response.startswith("ERROR:"):
        return None
    
    pro_forma = extract_json_from_response(raw_response)
    
    if pro_forma is not None:
        return pro_forma
    
    # Retry once with simplified prompt
    retry_message = message + "\n\nIMPORTANT: Your previous response could not be parsed as JSON. Return ONLY the JSON object with no other text."
    raw_response = call_claude(GENERATION_SYSTEM_PROMPT, retry_message, max_tokens=4096)
    
    if raw_response.startswith("ERROR:"):
        return None
    
    return extract_json_from_response(raw_response)


def _build_answer_summary(pro_forma: dict, calc_results: dict, warnings: list[str]) -> str:
    """
    Build a plain-English summary of the pro forma.
    
    Args:
        pro_forma: The generated pro forma dict.
        calc_results: Results from the return calculator.
        warnings: Any discrepancy warnings.
    
    Returns:
        3-5 sentence summary string.
    """
    summary = pro_forma.get("project_summary", {})
    costs = pro_forma.get("cost_assumptions", {})
    returns = pro_forma.get("return_metrics", {})
    
    deal_name = summary.get("deal_name", "Your project")
    market = summary.get("market", "unknown market")
    program = summary.get("program_type", "development")
    
    # Extract values safely
    def val(section, key, default=None):
        field = section.get(key, {})
        if isinstance(field, dict):
            return field.get("value", default)
        return default
    
    total_cost = val(costs, "total_project_cost")
    hard_cost_psf = val(costs, "hard_cost_psf")
    irr = val(returns, "project_irr_levered_pct")
    multiple = val(returns, "equity_multiple_lp")
    cap_rate = val(returns, "exit_cap_rate_pct")
    
    unit_count = val(summary, "unit_count")
    total_gfa = val(summary, "total_gfa_sf")
    
    # Build summary
    parts = []
    
    # Opening sentence
    size_desc = f"{unit_count:,} units" if unit_count else f"{total_gfa:,} SF" if total_gfa else ""
    if size_desc:
        parts.append(f"{deal_name} ({size_desc})")
    else:
        parts.append(deal_name)
    
    # Return metrics
    if irr and multiple:
        parts.append(f"projects a levered LP IRR of {irr:.1f}% and {multiple:.2f}x equity multiple")
    
    # Cost summary
    if total_cost:
        parts.append(f"on a total project cost of ${total_cost/1_000_000:.1f}M")
    
    # Construction cost
    if hard_cost_psf:
        parts.append(f"Construction cost is estimated at ${hard_cost_psf:.0f}/sf")
    
    # Exit assumptions
    if cap_rate:
        parts.append(f"Exit is modeled at a {cap_rate:.2f}% cap rate")
    
    answer = ". ".join(parts) + "."
    
    # Add warnings
    if warnings:
        answer += "\n\nNOTE: " + " ".join(warnings)
    
    answer += "\n\nAll revenue and cost assumptions are estimated from market data -- review with your broker before committing to an underwrite."
    
    return answer


def run(query: str) -> AgentResponse:
    """
    Main entry point for the financial agent.
    
    Orchestrates the full pipeline: extraction -> context -> generation -> validation.
    
    Args:
        query: User's natural language project description.
    
    Returns:
        AgentResponse with the pro forma and summary.
    """
    # Import calculator here to avoid circular imports
    from FallonPrototype.shared.return_calculator import compute_returns, check_return_discrepancy
    
    # 1. Extract and normalize parameters
    params = normalize_parameters(extract_parameters(query))
    
    # 2. Check for missing required params
    missing = check_missing_parameters(params)
    if missing:
        return AgentResponse(
            intent="FINANCIAL_MODEL",
            answer=format_clarification_message(missing),
            sources=[],
            raw_chunks=[],
            confidence="low",
            export_data=None,
            needs_clarification=True,
        )
    
    # 3. Retrieve context
    deal_comps = retrieve_deal_comps(params)
    defaults_dict = get_defaults_for_params(params)
    defaults_chunks = retrieve_defaults_context(params)
    
    # 4. Format context
    context = format_financial_context(deal_comps, defaults_dict, defaults_chunks, params)
    fallback_warning = get_fallback_warning(defaults_dict, params.market or "unknown")
    
    # 5. Generate pro forma
    pro_forma = generate_pro_forma(params, context)
    
    if pro_forma is None:
        return AgentResponse(
            intent="FINANCIAL_MODEL",
            answer="ERROR: Could not generate a valid pro forma. Please rephrase your request or provide more details.",
            sources=[],
            raw_chunks=[],
            confidence="low",
            export_data=None,
        )
    
    # 6. Validate
    is_valid, validation_errors = validate_pro_forma(pro_forma)
    
    # 7. Cross-check returns
    calc_results = compute_returns(pro_forma)
    warnings = check_return_discrepancy(pro_forma, calc_results)
    
    if fallback_warning:
        warnings.insert(0, fallback_warning)
    
    if not is_valid:
        warnings.append(f"Schema validation warnings: {', '.join(validation_errors[:3])}")
    
    # 8. Determine confidence
    has_high_comps = any(c.get("relevance") == "high" for c in deal_comps)
    has_market_data = defaults_dict is not None and not defaults_dict.get("_fallback")
    
    if has_high_comps and has_market_data:
        confidence = "high"
    elif has_market_data:
        confidence = "medium"
    else:
        confidence = "low"
    
    # 9. Build answer summary
    answer = _build_answer_summary(pro_forma, calc_results, warnings)
    
    return AgentResponse(
        intent="FINANCIAL_MODEL",
        answer=answer,
        sources=[c["metadata"]["source"] for c in deal_comps],
        raw_chunks=deal_comps,
        confidence=confidence,
        export_data={
            "pro_forma": pro_forma,
            "calc_results": calc_results,
            "warnings": warnings,
            "params": params_to_dict(params),
        },
        warnings=warnings,
    )
