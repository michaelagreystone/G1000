"""
Fallon — Development Intelligence

A minimal, Apple-inspired interface for real estate development analysis.
"""

import streamlit as st
import pandas as pd
import subprocess
import sys
import os
import copy
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from FallonPrototype.agents.financial_agent import (
    run,
    extract_parameters,
    normalize_parameters,
    merge_clarification,
    check_missing_parameters,
    format_clarification_message,
    ProjectParameters,
    AgentResponse,
    retrieve_deal_comps,
    get_defaults_for_params,
    retrieve_defaults_context,
    format_financial_context,
    generate_pro_forma,
    validate_pro_forma,
)
from FallonPrototype.agents.contract_agent import answer_contract_question
from FallonPrototype.shared.vector_store import get_collection_counts
from FallonPrototype.shared.return_calculator import (
    compute_returns,
    check_return_discrepancy,
    compute_sensitivity_table,
    _val,
)
from FallonPrototype.shared.excel_export import export_pro_forma, get_suggested_filename
from FallonPrototype.shared.claude_client import call_claude


# ═══════════════════════════════════════════════════════════════════════════════
# Page Config & Apple-Inspired Styling
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Fallon",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global Reset */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main Container */
    .main .block-container {
        max-width: 900px;
        padding: 2rem 1rem 6rem 1rem;
        margin: 0 auto;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 500 !important;
        letter-spacing: -0.02em !important;
        color: #1d1d1f !important;
    }
    
    p, span, div {
        color: #1d1d1f;
        line-height: 1.5;
    }
    
    /* Hero Title */
    .hero-title {
        font-size: 3.5rem;
        font-weight: 600;
        letter-spacing: -0.03em;
        color: #1d1d1f;
        text-align: center;
        margin: 3rem 0 0.5rem 0;
        line-height: 1.1;
    }
    
    .hero-subtitle {
        font-size: 1.25rem;
        font-weight: 400;
        color: #86868b;
        text-align: center;
        margin-bottom: 3rem;
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        padding: 1.5rem 0 !important;
    }
    
    [data-testid="stChatMessageContent"] {
        background: transparent !important;
        padding: 0 !important;
    }
    
    /* User Message Bubble */
    [data-testid="stChatMessageContent"] p {
        font-size: 1.0625rem;
        line-height: 1.6;
    }
    
    /* Chat Input */
    .stChatInput {
        border: none !important;
    }
    
    .stChatInput > div {
        background: #f5f5f7 !important;
        border: 1px solid #d2d2d7 !important;
        border-radius: 24px !important;
        padding: 0.25rem 0.5rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stChatInput > div:focus-within {
        border-color: #0071e3 !important;
        box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.1) !important;
    }
    
    .stChatInput textarea {
        font-size: 1rem !important;
        color: #1d1d1f !important;
    }
    
    .stChatInput textarea::placeholder {
        color: #86868b !important;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e8e8ed;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        border-color: #d2d2d7;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 600;
        color: #1d1d1f;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.8125rem;
        font-weight: 500;
        color: #86868b;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    
    /* Pro Forma Card */
    .proforma-container {
        background: #fbfbfd;
        border: 1px solid #e8e8ed;
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
    }
    
    .proforma-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 1.5rem;
        letter-spacing: -0.02em;
    }
    
    /* Data Tables */
    .stDataFrame {
        border: none !important;
    }
    
    .stDataFrame > div {
        border-radius: 12px;
        overflow: hidden;
    }
    
    [data-testid="stDataFrame"] table {
        font-size: 0.875rem !important;
    }
    
    [data-testid="stDataFrame"] th {
        background: #f5f5f7 !important;
        font-weight: 500 !important;
        color: #1d1d1f !important;
        border: none !important;
        padding: 0.75rem 1rem !important;
    }
    
    [data-testid="stDataFrame"] td {
        border: none !important;
        border-bottom: 1px solid #f0f0f0 !important;
        padding: 0.75rem 1rem !important;
        color: #1d1d1f !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #0071e3 !important;
        color: white !important;
        border: none !important;
        border-radius: 980px !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 0.9375rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0 !important;
    }
    
    .stButton > button:hover {
        background: #0077ed !important;
        transform: scale(1.02);
    }
    
    .stButton > button:active {
        transform: scale(0.98);
    }
    
    /* Secondary Button */
    .secondary-btn > button {
        background: transparent !important;
        color: #0071e3 !important;
        border: 1px solid #0071e3 !important;
    }
    
    .secondary-btn > button:hover {
        background: rgba(0, 113, 227, 0.04) !important;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: #1d1d1f !important;
        color: white !important;
        border: none !important;
        border-radius: 980px !important;
        padding: 0.875rem 1.75rem !important;
        font-size: 0.9375rem !important;
        font-weight: 500 !important;
    }
    
    .stDownloadButton > button:hover {
        background: #333336 !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        font-size: 0.9375rem !important;
        font-weight: 500 !important;
        color: #1d1d1f !important;
        background: transparent !important;
        border: none !important;
        padding: 1rem 0 !important;
    }
    
    .streamlit-expanderContent {
        border: none !important;
        padding: 0 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
        background: #f5f5f7;
        border-radius: 10px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: #86868b !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #1d1d1f !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #0071e3 transparent transparent transparent !important;
    }
    
    /* Info/Warning Boxes */
    .stAlert {
        background: #f5f5f7 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
    }
    
    .stAlert > div {
        color: #1d1d1f !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #fbfbfd !important;
        border-right: 1px solid #e8e8ed !important;
    }
    
    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.5rem !important;
    }
    
    /* Sidebar Title */
    [data-testid="stSidebar"] h1 {
        font-size: 1.125rem !important;
        font-weight: 600 !important;
    }
    
    /* Metrics in Sidebar */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #1d1d1f !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        color: #86868b !important;
        text-transform: uppercase !important;
        letter-spacing: 0.02em !important;
    }
    
    /* Caption */
    .caption-text {
        font-size: 0.8125rem;
        color: #86868b;
        margin-top: 0.5rem;
    }
    
    /* Source Pills */
    .source-pill {
        display: inline-block;
        background: #f5f5f7;
        color: #86868b;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.25rem 0.75rem;
        border-radius: 100px;
        margin-right: 0.5rem;
        margin-top: 0.5rem;
    }
    
    /* Confidence Indicator */
    .confidence-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .confidence-high { background: #34c759; }
    .confidence-medium { background: #ff9f0a; }
    .confidence-low { background: #ff3b30; }
    
    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
    }
    
    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.3;
    }
    
    .empty-state-text {
        color: #86868b;
        font-size: 1.0625rem;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #e8e8ed;
        margin: 2rem 0;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #d2d2d7;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #86868b;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Session State
# ═══════════════════════════════════════════════════════════════════════════════

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_clarification" not in st.session_state:
    st.session_state.pending_clarification = None
if "current_pro_forma" not in st.session_state:
    st.session_state.current_pro_forma = None
if "current_params" not in st.session_state:
    st.session_state.current_params = None


# ═══════════════════════════════════════════════════════════════════════════════
# Intent Classification
# ═══════════════════════════════════════════════════════════════════════════════

INTENT_PROMPT = """You are a real estate assistant. Classify the user's intent.

Return ONLY one word:
- PRO_FORMA: Generate financial model, pro forma, underwriting, development analysis
- QUESTION: Question about markets, contracts, deals, terms, or information
- ADJUSTMENT: Modify existing pro forma (change cap rate, rent, costs)
- CLARIFICATION: Providing additional information for a pending request

User message: {message}

Intent:"""


def classify_intent(message: str, has_pending: bool = False) -> str:
    if has_pending:
        return "CLARIFICATION"
    
    response = call_claude(
        "Return only: PRO_FORMA, QUESTION, ADJUSTMENT, or CLARIFICATION",
        INTENT_PROMPT.format(message=message),
        max_tokens=20,
    )
    
    intent = response.strip().upper()
    if intent in ["PRO_FORMA", "QUESTION", "ADJUSTMENT", "CLARIFICATION"]:
        return intent
    
    msg_lower = message.lower()
    pro_forma_keywords = ["generate", "model", "pro forma", "underwrite", "build", "unit", "keys", "sf "]
    if any(kw in msg_lower for kw in pro_forma_keywords):
        return "PRO_FORMA"
    
    return "QUESTION"


# ═══════════════════════════════════════════════════════════════════════════════
# Response Handlers
# ═══════════════════════════════════════════════════════════════════════════════

def handle_pro_forma_request(user_message: str) -> dict:
    response = run(user_message)
    
    if response.needs_clarification:
        params = normalize_parameters(extract_parameters(user_message))
        st.session_state.pending_clarification = {
            "type": "pro_forma",
            "params": params,
            "original_query": user_message,
        }
        return {
            "type": "clarification",
            "text": response.answer,
            "confidence": response.confidence,
        }
    
    if response.export_data and "pro_forma" in response.export_data:
        st.session_state.current_pro_forma = response.export_data
        st.session_state.pending_clarification = None
        return {
            "type": "pro_forma",
            "data": response.export_data,
            "sources": response.sources,
            "confidence": response.confidence,
            "warnings": response.warnings,
        }
    
    return {
        "type": "text",
        "text": response.answer,
        "confidence": response.confidence,
    }


def handle_clarification(user_message: str) -> dict:
    pending = st.session_state.pending_clarification
    
    if pending["type"] == "pro_forma":
        merged_params = merge_clarification(pending["params"], user_message)
        missing = check_missing_parameters(merged_params)
        
        if missing:
            st.session_state.pending_clarification["params"] = merged_params
            return {
                "type": "clarification",
                "text": format_clarification_message(missing),
            }
        
        deal_comps = retrieve_deal_comps(merged_params)
        defaults_dict = get_defaults_for_params(merged_params)
        defaults_chunks = retrieve_defaults_context(merged_params)
        context = format_financial_context(deal_comps, defaults_dict, defaults_chunks, merged_params)
        
        pro_forma = generate_pro_forma(merged_params, context)
        
        if pro_forma:
            calc_results = compute_returns(pro_forma)
            warnings = check_return_discrepancy(pro_forma, calc_results)
            
            export_data = {
                "pro_forma": pro_forma,
                "calc_results": calc_results,
                "warnings": warnings,
            }
            
            st.session_state.current_pro_forma = export_data
            st.session_state.pending_clarification = None
            
            return {
                "type": "pro_forma",
                "data": export_data,
                "sources": [c["metadata"]["source"] for c in deal_comps],
                "confidence": "medium",
                "warnings": warnings,
            }
        
        return {"type": "text", "text": "Unable to generate the model. Please try again."}
    
    return {"type": "text", "text": "Could you clarify what you need?"}


def handle_question(user_message: str) -> dict:
    response = answer_contract_question(user_message)
    
    return {
        "type": "answer",
        "text": response.answer,
        "sources": response.sources,
        "confidence": response.confidence,
        "chunks": response.chunks_used,
    }


def handle_adjustment(user_message: str) -> dict:
    if not st.session_state.current_pro_forma:
        return {
            "type": "text",
            "text": "No active model to adjust. Generate one first.",
        }
    
    adjustments = parse_adjustment_request(user_message)
    
    if not adjustments:
        return {
            "type": "text",
            "text": "Try: \"change cap rate to 5.5%\" or \"set rent to $2.50/sf\"",
        }
    
    adjusted = copy.deepcopy(st.session_state.current_pro_forma["pro_forma"])
    changes_made = []
    
    for field, value in adjustments.items():
        if apply_adjustment(adjusted, field, value):
            changes_made.append(f"{field.replace('_', ' ')}: {value}")
    
    new_calc = compute_returns(adjusted)
    warnings = check_return_discrepancy(adjusted, new_calc)
    
    st.session_state.current_pro_forma = {
        "pro_forma": adjusted,
        "calc_results": new_calc,
        "warnings": warnings,
    }
    
    return {
        "type": "pro_forma",
        "data": st.session_state.current_pro_forma,
        "text": f"Updated {', '.join(changes_made)}",
        "confidence": "high",
        "warnings": warnings,
    }


def parse_adjustment_request(message: str) -> dict:
    import re
    adjustments = {}
    msg_lower = message.lower()
    
    cap_match = re.search(r'cap\s*rate.*?(\d+\.?\d*)\s*%?', msg_lower)
    if cap_match:
        adjustments["exit_cap_rate"] = float(cap_match.group(1))
    
    rent_match = re.search(r'rent.*?\$?(\d+\.?\d*)', msg_lower)
    if rent_match:
        adjustments["rent_psf"] = float(rent_match.group(1))
    
    cost_match = re.search(r'(?:construction|hard)\s*cost.*?\$?(\d+)', msg_lower)
    if cost_match:
        adjustments["hard_cost_psf"] = float(cost_match.group(1))
    
    loan_match = re.search(r'(?:loan|interest)\s*rate.*?(\d+\.?\d*)\s*%?', msg_lower)
    if loan_match:
        adjustments["loan_rate"] = float(loan_match.group(1))
    
    return adjustments


def apply_adjustment(pro_forma: dict, field: str, value: float) -> bool:
    mapping = {
        "exit_cap_rate": ("return_metrics", "exit_cap_rate_pct"),
        "rent_psf": ("revenue_assumptions", "rent_psf_monthly"),
        "hard_cost_psf": ("cost_assumptions", "hard_cost_psf"),
        "loan_rate": ("financing_assumptions", "construction_loan_rate_pct"),
    }
    
    if field not in mapping:
        return False
    
    section, key = mapping[field]
    if section in pro_forma and key in pro_forma[section]:
        if isinstance(pro_forma[section][key], dict):
            pro_forma[section][key]["value"] = value
        else:
            pro_forma[section][key] = value
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Display Components
# ═══════════════════════════════════════════════════════════════════════════════

def display_pro_forma_card(data: dict):
    """Display a minimal pro forma card."""
    pro_forma = data.get("pro_forma", {})
    calc_results = data.get("calc_results", {})
    warnings = data.get("warnings", [])
    
    summary = pro_forma.get("project_summary", {})
    returns = pro_forma.get("return_metrics", {})
    costs = pro_forma.get("cost_assumptions", {})
    
    deal_name = _val(summary, "deal_name", "Development Model")
    
    # Container
    st.markdown(f'<div class="proforma-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="proforma-title">{deal_name}</div>', unsafe_allow_html=True)
    
    # Metrics
    irr = _val(returns, "project_irr_levered_pct")
    multiple = _val(returns, "equity_multiple_lp")
    poc = _val(returns, "profit_on_cost_pct")
    total_cost = _val(costs, "total_project_cost")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{f"{irr:.1f}%" if irr else "—"}</div>
            <div class="metric-label">LP IRR</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{f"{multiple:.2f}x" if multiple else "—"}</div>
            <div class="metric-label">Multiple</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{f"{poc:.1f}%" if poc else "—"}</div>
            <div class="metric-label">Profit on Cost</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{f"${total_cost/1_000_000:.0f}M" if total_cost else "—"}</div>
            <div class="metric-label">Total Cost</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Warnings
    for warning in warnings:
        st.warning(warning)
    
    # Details
    with st.expander("View Details"):
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Revenue", "Costs", "Financing", "Returns"])
        
        def section_to_df(section: dict) -> pd.DataFrame:
            rows = []
            for key, field in section.items():
                if isinstance(field, dict) and "value" in field:
                    val = field.get("value")
                    if isinstance(val, float):
                        val = f"{val:,.2f}" if val < 100 else f"{val:,.0f}"
                    rows.append({
                        "Item": key.replace("_", " ").title(),
                        "Value": val,
                        "Unit": field.get("unit", ""),
                    })
                elif field is not None and not isinstance(field, dict):
                    val = field
                    if isinstance(val, float):
                        val = f"{val:,.2f}" if val < 100 else f"{val:,.0f}"
                    rows.append({
                        "Item": key.replace("_", " ").title(),
                        "Value": val,
                        "Unit": "",
                    })
            return pd.DataFrame(rows) if rows else pd.DataFrame({"Item": [], "Value": [], "Unit": []})
        
        with tab1:
            st.dataframe(section_to_df(pro_forma.get("project_summary", {})), use_container_width=True, hide_index=True)
        with tab2:
            st.dataframe(section_to_df(pro_forma.get("revenue_assumptions", {})), use_container_width=True, hide_index=True)
        with tab3:
            st.dataframe(section_to_df(pro_forma.get("cost_assumptions", {})), use_container_width=True, hide_index=True)
        with tab4:
            st.dataframe(section_to_df(pro_forma.get("financing_assumptions", {})), use_container_width=True, hide_index=True)
        with tab5:
            st.dataframe(section_to_df(pro_forma.get("return_metrics", {})), use_container_width=True, hide_index=True)
    
    # Sensitivity
    with st.expander("Sensitivity"):
        target_irr = _val(returns, "lp_irr_pct", 14.0)
        sensitivity = compute_sensitivity_table(pro_forma, target_irr=target_irr)
        
        sens_data = {"Exit Cap": sensitivity["rows"]}
        for i, col_label in enumerate(sensitivity["cols"]):
            sens_data[col_label] = [
                f"{sensitivity['values'][j][i]:.1f}%" if sensitivity['values'][j][i] else "—"
                for j in range(3)
            ]
        st.dataframe(pd.DataFrame(sens_data), use_container_width=True, hide_index=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Download
    sensitivity = compute_sensitivity_table(pro_forma, target_irr=_val(returns, "lp_irr_pct", 14.0))
    export_data = {**data, "sensitivity": sensitivity}
    excel_bytes = export_pro_forma(export_data, deal_name)
    filename = get_suggested_filename(export_data)
    
    st.download_button(
        label="Download Model",
        data=excel_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    
    st.markdown('</div>', unsafe_allow_html=True)


def display_answer(text: str, sources: list, confidence: str):
    """Display a Q&A answer with minimal styling."""
    conf_class = f"confidence-{confidence}"
    
    st.markdown(text)
    
    if sources:
        st.markdown(f'''
        <div style="margin-top: 1rem;">
            <span class="confidence-dot {conf_class}"></span>
            <span style="font-size: 0.8125rem; color: #86868b;">{confidence.title()} confidence</span>
        </div>
        ''', unsafe_allow_html=True)
        
        pills_html = "".join(f'<span class="source-pill">{s}</span>' for s in sources[:3])
        st.markdown(f'<div>{pills_html}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### Settings")
    st.markdown("---")
    
    try:
        counts = get_collection_counts()
        st.caption("KNOWLEDGE BASE")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Contracts", counts.get("fallon_contracts", 0))
            st.metric("Research", counts.get("fallon_market_research", 0))
        with col2:
            st.metric("Deals", counts.get("fallon_deal_data", 0))
            st.metric("Defaults", counts.get("fallon_market_defaults", 0))
    except Exception:
        pass
    
    st.markdown("---")
    
    if st.button("Reindex Data", use_container_width=True):
        with st.spinner(""):
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "FallonPrototype.shared.run_all_ingestion"],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                )
                st.success("Done" if result.returncode == 0 else "Failed")
            except Exception:
                st.error("Error")
    
    st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_clarification = None
        st.session_state.current_pro_forma = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("EXAMPLES")
    st.markdown("""
    <div style="font-size: 0.8125rem; color: #86868b; line-height: 1.8;">
    200 unit multifamily in Charlotte<br>
    What are Boston cap rates?<br>
    How does a waterfall work?<br>
    Change cap rate to 5.5%
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Main Interface
# ═══════════════════════════════════════════════════════════════════════════════

# Hero (only show if no messages)
if not st.session_state.messages:
    st.markdown('''
    <div class="hero-title">Fallon</div>
    <div class="hero-subtitle">Development intelligence for real estate</div>
    ''', unsafe_allow_html=True)
    
    # Suggestion chips
    col1, col2, col3 = st.columns(3)
    
    suggestions = [
        "200 unit multifamily in Charlotte",
        "What are cap rates in Boston?",
        "How does a JV waterfall work?",
    ]
    
    for i, (col, suggestion) in enumerate(zip([col1, col2, col3], suggestions)):
        with col:
            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": suggestion})
                st.rerun()

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="◼" if msg["role"] == "assistant" else None):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            response = msg.get("response", {})
            
            if response.get("type") == "pro_forma":
                if response.get("text"):
                    st.markdown(response["text"])
                display_pro_forma_card(response["data"])
            
            elif response.get("type") == "answer":
                display_answer(
                    response["text"],
                    response.get("sources", []),
                    response.get("confidence", "medium"),
                )
            
            elif response.get("type") == "clarification":
                st.markdown(response["text"])
            
            else:
                st.markdown(msg.get("content", response.get("text", "")))

# Chat input
if prompt := st.chat_input("Ask anything about real estate development..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant", avatar="◼"):
        with st.spinner(""):
            try:
                has_pending = st.session_state.pending_clarification is not None
                intent = classify_intent(prompt, has_pending)
                
                if intent == "CLARIFICATION" and has_pending:
                    response = handle_clarification(prompt)
                elif intent == "PRO_FORMA":
                    response = handle_pro_forma_request(prompt)
                elif intent == "ADJUSTMENT":
                    response = handle_adjustment(prompt)
                else:
                    response = handle_question(prompt)
                
                if response["type"] == "pro_forma":
                    if response.get("text"):
                        st.markdown(response["text"])
                    display_pro_forma_card(response["data"])
                
                elif response["type"] == "answer":
                    display_answer(
                        response["text"],
                        response.get("sources", []),
                        response.get("confidence", "medium"),
                    )
                
                elif response["type"] == "clarification":
                    st.markdown(response["text"])
                
                else:
                    st.markdown(response.get("text", ""))
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "response": response,
                    "content": response.get("text", ""),
                })
                
            except Exception:
                error_msg = "Something went wrong. Please try again."
                st.markdown(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "response": {"type": "text", "text": error_msg},
                })
