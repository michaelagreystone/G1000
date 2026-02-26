"""
FALLON Memory System

Persistent learning from user interactions:
- Stores query history and outcomes
- Tracks user preferences and patterns
- Learns from adjustments and corrections
- Provides context for improved responses
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import Counter

MEMORY_DIR = Path(__file__).parent.parent / "data" / "memory"
MEMORY_FILE = MEMORY_DIR / "user_memory.json"
INSIGHTS_FILE = MEMORY_DIR / "learned_insights.json"

def _ensure_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

def _load_memory() -> dict:
    _ensure_dir()
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text())
        except:
            return _default_memory()
    return _default_memory()

def _save_memory(data: dict):
    _ensure_dir()
    MEMORY_FILE.write_text(json.dumps(data, indent=2, default=str))

def _default_memory() -> dict:
    return {
        "interactions": [],
        "preferences": {
            "markets": {},
            "program_types": {},
            "typical_deal_size": None,
            "target_irr_range": [15, 20],
            "preferred_exit_cap": None,
        },
        "corrections": [],
        "successful_queries": [],
        "learned_defaults": {},
        "feedback_scores": [],
    }

# ═══════════════════════════════════════════════════════════════════════════════
# RECORD INTERACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def record_interaction(
    query: str,
    intent: str,
    response_type: str,
    parameters: dict = None,
    pro_forma: dict = None,
    sources_used: list = None,
    success: bool = True,
):
    """Record a user interaction for learning."""
    memory = _load_memory()
    
    interaction = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "intent": intent,
        "response_type": response_type,
        "parameters": parameters or {},
        "sources_used": sources_used or [],
        "success": success,
    }
    
    # Extract key metrics if pro forma was generated
    if pro_forma:
        interaction["metrics"] = {
            "irr": _extract_val(pro_forma, "return_metrics", "project_irr_levered_pct"),
            "multiple": _extract_val(pro_forma, "return_metrics", "equity_multiple_lp"),
            "exit_cap": _extract_val(pro_forma, "return_metrics", "exit_cap_rate_pct"),
            "total_cost": _extract_val(pro_forma, "cost_assumptions", "total_project_cost"),
        }
        interaction["deal_name"] = _extract_val(pro_forma, "project_summary", "deal_name")
        interaction["market"] = _extract_val(pro_forma, "project_summary", "market")
        interaction["program_type"] = _extract_val(pro_forma, "project_summary", "program_type")
    
    memory["interactions"].append(interaction)
    
    # Keep last 500 interactions
    memory["interactions"] = memory["interactions"][-500:]
    
    # Update preferences based on this interaction
    _update_preferences(memory, interaction)
    
    if success:
        memory["successful_queries"].append({
            "query": query,
            "timestamp": interaction["timestamp"],
        })
        memory["successful_queries"] = memory["successful_queries"][-100:]
    
    _save_memory(memory)
    
    # Periodically analyze and extract insights
    if len(memory["interactions"]) % 10 == 0:
        analyze_and_learn()

def record_adjustment(
    original_param: str,
    original_value: float,
    adjusted_value: float,
    context: dict = None,
):
    """Record when user adjusts a parameter - key learning signal."""
    memory = _load_memory()
    
    correction = {
        "timestamp": datetime.now().isoformat(),
        "parameter": original_param,
        "original": original_value,
        "adjusted": adjusted_value,
        "delta": adjusted_value - original_value if original_value else None,
        "context": context or {},
    }
    
    memory["corrections"].append(correction)
    memory["corrections"] = memory["corrections"][-200:]
    
    # Learn from this correction
    _learn_from_correction(memory, correction)
    
    _save_memory(memory)

def record_feedback(query: str, helpful: bool, notes: str = ""):
    """Record explicit user feedback."""
    memory = _load_memory()
    
    memory["feedback_scores"].append({
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "helpful": helpful,
        "notes": notes,
    })
    memory["feedback_scores"] = memory["feedback_scores"][-100:]
    
    _save_memory(memory)

# ═══════════════════════════════════════════════════════════════════════════════
# LEARNING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _update_preferences(memory: dict, interaction: dict):
    """Update user preferences based on interaction patterns."""
    prefs = memory["preferences"]
    
    # Track market preferences
    market = interaction.get("market")
    if market:
        prefs["markets"][market] = prefs["markets"].get(market, 0) + 1
    
    # Track program type preferences
    prog = interaction.get("program_type")
    if prog:
        prefs["program_types"][prog] = prefs["program_types"].get(prog, 0) + 1
    
    # Track typical deal sizes
    metrics = interaction.get("metrics", {})
    if metrics.get("total_cost"):
        costs = [i.get("metrics", {}).get("total_cost") for i in memory["interactions"] if i.get("metrics", {}).get("total_cost")]
        if costs:
            prefs["typical_deal_size"] = sum(costs) / len(costs)
    
    # Track IRR expectations
    if metrics.get("irr"):
        irrs = [i.get("metrics", {}).get("irr") for i in memory["interactions"] if i.get("metrics", {}).get("irr")]
        if len(irrs) >= 3:
            prefs["target_irr_range"] = [min(irrs), max(irrs)]

def _learn_from_correction(memory: dict, correction: dict):
    """Learn default adjustments from user corrections."""
    param = correction["parameter"]
    delta = correction.get("delta")
    context = correction.get("context", {})
    
    if delta is None:
        return
    
    # Build context key (market + program type)
    market = context.get("market", "general")
    prog = context.get("program_type", "general")
    key = f"{market}_{prog}_{param}"
    
    # Track correction patterns
    learned = memory.get("learned_defaults", {})
    if key not in learned:
        learned[key] = {"deltas": [], "avg_adjustment": 0}
    
    learned[key]["deltas"].append(delta)
    learned[key]["deltas"] = learned[key]["deltas"][-20:]  # Keep last 20
    learned[key]["avg_adjustment"] = sum(learned[key]["deltas"]) / len(learned[key]["deltas"])
    
    memory["learned_defaults"] = learned

def analyze_and_learn():
    """Analyze interaction history and extract insights."""
    memory = _load_memory()
    interactions = memory["interactions"]
    
    if len(interactions) < 5:
        return
    
    insights = {
        "generated_at": datetime.now().isoformat(),
        "total_interactions": len(interactions),
        "patterns": {},
    }
    
    # Most common markets
    markets = [i.get("market") for i in interactions if i.get("market")]
    if markets:
        insights["patterns"]["top_markets"] = Counter(markets).most_common(5)
    
    # Most common program types
    programs = [i.get("program_type") for i in interactions if i.get("program_type")]
    if programs:
        insights["patterns"]["top_programs"] = Counter(programs).most_common(5)
    
    # Average deal metrics
    irrs = [i.get("metrics", {}).get("irr") for i in interactions if i.get("metrics", {}).get("irr")]
    caps = [i.get("metrics", {}).get("exit_cap") for i in interactions if i.get("metrics", {}).get("exit_cap")]
    costs = [i.get("metrics", {}).get("total_cost") for i in interactions if i.get("metrics", {}).get("total_cost")]
    
    if irrs:
        insights["patterns"]["avg_irr"] = sum(irrs) / len(irrs)
    if caps:
        insights["patterns"]["avg_exit_cap"] = sum(caps) / len(caps)
    if costs:
        insights["patterns"]["avg_deal_size"] = sum(costs) / len(costs)
    
    # Common query patterns
    intents = [i.get("intent") for i in interactions if i.get("intent")]
    if intents:
        insights["patterns"]["intent_distribution"] = dict(Counter(intents))
    
    # Success rate
    successes = [i for i in interactions if i.get("success")]
    insights["patterns"]["success_rate"] = len(successes) / len(interactions) if interactions else 0
    
    # Correction patterns
    corrections = memory.get("corrections", [])
    if corrections:
        param_corrections = Counter([c["parameter"] for c in corrections])
        insights["patterns"]["most_corrected_params"] = param_corrections.most_common(5)
    
    # Save insights
    _ensure_dir()
    INSIGHTS_FILE.write_text(json.dumps(insights, indent=2))
    
    return insights

# ═══════════════════════════════════════════════════════════════════════════════
# RETRIEVAL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_user_context() -> dict:
    """Get accumulated user context for improving responses."""
    memory = _load_memory()
    prefs = memory["preferences"]
    
    context = {
        "has_history": len(memory["interactions"]) > 0,
        "interaction_count": len(memory["interactions"]),
    }
    
    # Preferred markets (sorted by frequency)
    if prefs["markets"]:
        context["preferred_markets"] = sorted(
            prefs["markets"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
    
    # Preferred program types
    if prefs["program_types"]:
        context["preferred_programs"] = sorted(
            prefs["program_types"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
    
    # Typical deal parameters
    if prefs["typical_deal_size"]:
        context["typical_deal_size"] = prefs["typical_deal_size"]
    
    context["target_irr_range"] = prefs["target_irr_range"]
    
    if prefs["preferred_exit_cap"]:
        context["preferred_exit_cap"] = prefs["preferred_exit_cap"]
    
    return context

def get_learned_adjustment(param: str, market: str = None, program: str = None) -> Optional[float]:
    """Get learned adjustment for a parameter based on past corrections."""
    memory = _load_memory()
    learned = memory.get("learned_defaults", {})
    
    # Try specific key first
    if market and program:
        key = f"{market}_{program}_{param}"
        if key in learned:
            return learned[key].get("avg_adjustment")
    
    # Try market-specific
    if market:
        key = f"{market}_general_{param}"
        if key in learned:
            return learned[key].get("avg_adjustment")
    
    # Try general
    key = f"general_general_{param}"
    if key in learned:
        return learned[key].get("avg_adjustment")
    
    return None

def get_similar_past_queries(query: str, limit: int = 3) -> list:
    """Find similar past successful queries for context."""
    memory = _load_memory()
    successful = memory.get("successful_queries", [])
    
    # Simple keyword matching (could be enhanced with embeddings)
    query_words = set(query.lower().split())
    
    scored = []
    for past in successful:
        past_words = set(past["query"].lower().split())
        overlap = len(query_words & past_words)
        if overlap > 0:
            scored.append((past, overlap))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:limit]]

def get_recent_pro_formas(limit: int = 5) -> list:
    """Get recent pro forma generations for reference."""
    memory = _load_memory()
    
    pro_formas = [
        i for i in memory["interactions"]
        if i.get("response_type") == "model" and i.get("metrics")
    ]
    
    return pro_formas[-limit:]

def format_context_for_prompt() -> str:
    """Format user context as a string for inclusion in prompts."""
    ctx = get_user_context()
    
    if not ctx.get("has_history"):
        return ""
    
    lines = ["USER CONTEXT (learned from past interactions):"]
    
    if ctx.get("preferred_markets"):
        markets = ", ".join([m[0] for m in ctx["preferred_markets"]])
        lines.append(f"- Frequently analyzes: {markets}")
    
    if ctx.get("preferred_programs"):
        programs = ", ".join([p[0] for p in ctx["preferred_programs"]])
        lines.append(f"- Common deal types: {programs}")
    
    if ctx.get("typical_deal_size"):
        size = ctx["typical_deal_size"]
        lines.append(f"- Typical deal size: ${size/1e6:.0f}M")
    
    if ctx.get("target_irr_range"):
        low, high = ctx["target_irr_range"]
        lines.append(f"- Target IRR range: {low:.0f}% - {high:.0f}%")
    
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_val(data: dict, section: str, key: str):
    """Extract value from nested pro forma structure."""
    if not data:
        return None
    sec = data.get(section, {})
    if not sec:
        return None
    field = sec.get(key)
    if field is None:
        return None
    if isinstance(field, dict):
        return field.get("value")
    return field

def clear_memory():
    """Clear all stored memory (for testing/reset)."""
    _save_memory(_default_memory())
    if INSIGHTS_FILE.exists():
        INSIGHTS_FILE.unlink()
