"""
FAiLLON — Development Intelligence Platform
"""

import streamlit as st
import pandas as pd
import json
import subprocess
import sys
import os
import copy
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from FallonPrototype.agents.financial_agent import (
    run, extract_parameters, normalize_parameters, merge_clarification,
    check_missing_parameters, format_clarification_message, retrieve_deal_comps,
    get_defaults_for_params, retrieve_defaults_context, format_financial_context,
    generate_pro_forma,
)
from FallonPrototype.agents.contract_agent import answer_contract_question
from FallonPrototype.shared.vector_store import get_collection_counts
from FallonPrototype.shared.return_calculator import compute_returns, check_return_discrepancy, compute_sensitivity_table, _val
from FallonPrototype.shared.excel_export import export_pro_forma, get_suggested_filename
from FallonPrototype.shared.memory import (
    record_interaction, record_adjustment, get_user_context,
    get_learned_adjustment, format_context_for_prompt, analyze_and_learn
)

st.set_page_config(page_title="FAiLLON", page_icon="◼", layout="wide", initial_sidebar_state="expanded")

# ChatGPT-style dark theme with wide centered input
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }

/* Pure black background */
.stApp { background: #000000 !important; }
.main .block-container { max-width: 900px; padding: 1rem 2rem 7rem 2rem; }

/* Typography */
h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
p, span, li, label { color: #d1d5db; }

/* Sidebar - Chat history panel */
[data-testid="stSidebar"] { 
    background: #171717 !important; 
    border-right: 1px solid #2a2a2a !important;
    width: 260px !important;
}
[data-testid="stSidebar"] * { color: #d1d5db !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #ffffff !important; }
[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.1rem !important; }
[data-testid="stMetricLabel"] { color: #6b7280 !important; font-size: 0.65rem !important; text-transform: uppercase !important; }

/* Suggestion buttons - pill style */
.stButton > button {
    background: #2f2f2f !important;
    color: #d1d5db !important;
    border: 1px solid #404040 !important;
    border-radius: 24px !important;
    padding: 0.6rem 1rem !important;
    font-size: 0.875rem !important;
    font-weight: 400 !important;
}
.stButton > button:hover {
    background: #404040 !important;
    border-color: #525252 !important;
    color: #ffffff !important;
}

/* Download buttons */
.stDownloadButton > button {
    background: #10a37f !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
.stDownloadButton > button:hover { background: #1a7f64 !important; }

/* Chat messages */
[data-testid="stChatMessage"] { background: transparent !important; padding: 1rem 0 !important; }
[data-testid="stChatMessageContent"] { background: transparent !important; padding: 0.5rem 0 !important; border: none !important; }
[data-testid="stChatMessageContent"] p { color: #ececec !important; font-size: 0.9375rem !important; line-height: 1.6 !important; }

/* CHAT INPUT - Wide centered grey bar, white text, NO highlight */
.stBottom, [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { 
    background: #000000 !important; 
    padding: 1.5rem 2rem !important;
}

[data-testid="stChatInput"],
.stChatInput {
    max-width: 900px !important;
    margin: 0 auto !important;
}

[data-testid="stChatInput"] > div,
.stChatInput > div {
    background: #303030 !important;
    border: none !important;
    border-radius: 26px !important;
    padding: 0.25rem 0.5rem !important;
    box-shadow: none !important;
    outline: none !important;
}

[data-testid="stChatInput"] > div:focus-within,
.stChatInput > div:focus-within {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

[data-testid="stChatInput"] textarea,
.stChatInput textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: transparent !important;
    font-size: 1rem !important;
    caret-color: #ffffff !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] textarea:focus,
.stChatInput textarea:focus {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] textarea::placeholder,
.stChatInput textarea::placeholder {
    color: #6b7280 !important;
    -webkit-text-fill-color: #6b7280 !important;
}

/* Remove any focus rings or highlights */
*:focus { outline: none !important; box-shadow: none !important; }
textarea:focus, input:focus { outline: none !important; box-shadow: none !important; }

/* Metric cards */
.metric-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.metric-value { font-size: 1.5rem; font-weight: 600; color: #ffffff; }
.metric-label { font-size: 0.6875rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }

/* Tables */
[data-testid="stDataFrame"] { background: transparent !important; }
[data-testid="stDataFrame"] table { background: #1a1a1a !important; border-radius: 8px !important; }
[data-testid="stDataFrame"] th { background: #2a2a2a !important; color: #9ca3af !important; font-size: 0.75rem !important; text-transform: uppercase !important; }
[data-testid="stDataFrame"] td { background: #1a1a1a !important; color: #ececec !important; border-bottom: 1px solid #2a2a2a !important; }

/* Expanders */
.streamlit-expanderHeader { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; border-radius: 8px !important; color: #ececec !important; }
.streamlit-expanderContent { background: #141414 !important; border: 1px solid #2a2a2a !important; border-top: none !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #1a1a1a; border-radius: 8px; padding: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #6b7280 !important; border-radius: 6px !important; font-size: 0.8125rem !important; }
.stTabs [aria-selected="true"] { background: #2a2a2a !important; color: #ffffff !important; }

/* Alerts */
.stAlert { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; border-radius: 8px !important; }

/* Hero */
.hero { text-align: center; padding: 4rem 1rem 2rem 1rem; }
.hero h1 { font-size: 2.5rem; color: #ffffff; margin-bottom: 0.5rem; letter-spacing: -0.02em; }
.hero p { color: #6b7280; font-size: 1rem; }

/* Source tags */
.src-tag { display: inline-block; background: #2a2a2a; color: #9ca3af; font-size: 0.6875rem; padding: 0.2rem 0.5rem; border-radius: 4px; margin-right: 0.4rem; }

/* Chat history item */
.chat-item { 
    padding: 0.6rem 0.75rem; 
    margin: 0.25rem 0; 
    border-radius: 8px; 
    cursor: pointer;
    color: #d1d5db;
    font-size: 0.875rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.chat-item:hover { background: #2a2a2a; }
</style>
""", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None
if "model" not in st.session_state:
    st.session_state.model = None
if "run_query" not in st.session_state:
    st.session_state.run_query = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Fast intent classification
def classify(msg):
    if st.session_state.pending:
        return "CLARIFY"
    m = msg.lower()
    if any(k in m for k in ["unit", "sf", "key", "room", "underwrite", "model", "pro forma", "generate", "build", "mf", "multifamily"]):
        return "MODEL"
    if st.session_state.model and any(k in m for k in ["change", "adjust", "set", "update", "modify"]):
        return "ADJUST"
    return "QUERY"

# Process and generate response with memory/learning
def process(msg):
    intent = classify(msg)
    user_ctx = get_user_context()  # Get learned context
    
    if intent == "CLARIFY":
        p = st.session_state.pending
        merged = merge_clarification(p["p"], msg)
        missing = check_missing_parameters(merged)
        if missing:
            st.session_state.pending["p"] = merged
            record_interaction(msg, intent, "clarify", parameters=merged)
            return {"t": "clarify", "txt": format_clarification_message(missing)}
        comps = retrieve_deal_comps(merged)
        ctx = format_financial_context(comps, get_defaults_for_params(merged), retrieve_defaults_context(merged), merged)
        pf = generate_pro_forma(merged, ctx)
        if pf:
            calc = compute_returns(pf)
            data = {"pro_forma": pf, "calc_results": calc, "warnings": check_return_discrepancy(pf, calc)}
            st.session_state.model = data
            st.session_state.pending = None
            # Record successful model generation
            record_interaction(msg, intent, "model", parameters=merged, pro_forma=pf, success=True)
            return {"t": "model", "data": data}
        record_interaction(msg, intent, "error", success=False)
        return {"t": "txt", "txt": "Could not generate model."}
    
    elif intent == "MODEL":
        # Add user context to the request
        r = run(msg, user_context=user_ctx)
        if r.needs_clarification:
            st.session_state.pending = {"p": normalize_parameters(extract_parameters(msg))}
            record_interaction(msg, intent, "clarify")
            return {"t": "clarify", "txt": r.answer}
        if r.export_data and "pro_forma" in r.export_data:
            st.session_state.model = r.export_data
            st.session_state.pending = None
            # Record successful model with all data for learning
            record_interaction(
                msg, intent, "model",
                pro_forma=r.export_data.get("pro_forma"),
                sources_used=r.sources,
                success=True
            )
            return {"t": "model", "data": r.export_data}
        record_interaction(msg, intent, "text", success=True)
        return {"t": "txt", "txt": r.answer}
    
    elif intent == "ADJUST":
        if not st.session_state.model:
            return {"t": "txt", "txt": "No model to adjust."}
        pf = copy.deepcopy(st.session_state.model["pro_forma"])
        changes = []
        m = msg.lower()
        
        # Get context for learning
        market = _val(pf.get("project_summary", {}), "market")
        prog = _val(pf.get("project_summary", {}), "program_type")
        
        if cap := re.search(r'cap.*?(\d+\.?\d*)', m):
            v = float(cap.group(1))
            if "return_metrics" in pf:
                old_val = _val(pf["return_metrics"], "exit_cap_rate_pct")
                pf["return_metrics"]["exit_cap_rate_pct"] = v
                changes.append(f"cap {v}%")
                # Record this adjustment for learning
                record_adjustment("exit_cap_rate_pct", old_val, v, {"market": market, "program_type": prog})
                
        if rent := re.search(r'rent.*?\$?(\d+\.?\d*)', m):
            v = float(rent.group(1))
            if "revenue_assumptions" in pf:
                old_val = _val(pf["revenue_assumptions"], "rent_psf_monthly")
                pf["revenue_assumptions"]["rent_psf_monthly"] = v
                changes.append(f"rent ${v}")
                record_adjustment("rent_psf_monthly", old_val, v, {"market": market, "program_type": prog})
                
        if changes:
            calc = compute_returns(pf)
            st.session_state.model = {"pro_forma": pf, "calc_results": calc, "warnings": check_return_discrepancy(pf, calc)}
            record_interaction(msg, intent, "model", pro_forma=pf, success=True)
            return {"t": "model", "data": st.session_state.model, "txt": f"Adjusted: {', '.join(changes)}"}
        return {"t": "txt", "txt": "Specify: 'cap 5.25' or 'rent 2.85'"}
    
    else:  # QUERY
        r = answer_contract_question(msg)
        record_interaction(msg, intent, "answer", sources_used=r.sources, success=True)
        return {"t": "answer", "txt": r.answer, "src": r.sources, "conf": r.confidence}

# Render model output
def show_model(data, note=None):
    pf = data.get("pro_forma", {})
    ret = pf.get("return_metrics", {})
    cost = pf.get("cost_assumptions", {})
    name = _val(pf.get("project_summary", {}), "deal_name", "Model")
    
    if note:
        st.caption(note)
    
    st.markdown(f"**{name}**")
    
    c1, c2, c3, c4 = st.columns(4)
    irr, mult, poc, tc = _val(ret, "project_irr_levered_pct"), _val(ret, "equity_multiple_lp"), _val(ret, "profit_on_cost_pct"), _val(cost, "total_project_cost")
    
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{f"{irr:.1f}%" if irr else "—"}</div><div class="metric-label">IRR</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{f"{mult:.2f}x" if mult else "—"}</div><div class="metric-label">Multiple</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{f"{poc:.1f}%" if poc else "—"}</div><div class="metric-label">Margin</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{f"${tc/1e6:.0f}M" if tc else "—"}</div><div class="metric-label">Cost</div></div>', unsafe_allow_html=True)
    
    for w in data.get("warnings", []):
        st.warning(w)
    
    with st.expander("Details"):
        tabs = st.tabs(["Summary", "Revenue", "Cost", "Capital", "Returns"])
        def df(s):
            rows = [{"Field": k.replace("_"," ").title(), "Value": (v.get("value") if isinstance(v,dict) else v)} for k,v in s.items() if (v.get("value") if isinstance(v,dict) else v) is not None]
            return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Field","Value"])
        with tabs[0]: st.dataframe(df(pf.get("project_summary",{})), use_container_width=True, hide_index=True)
        with tabs[1]: st.dataframe(df(pf.get("revenue_assumptions",{})), use_container_width=True, hide_index=True)
        with tabs[2]: st.dataframe(df(pf.get("cost_assumptions",{})), use_container_width=True, hide_index=True)
        with tabs[3]: st.dataframe(df(pf.get("financing_assumptions",{})), use_container_width=True, hide_index=True)
        with tabs[4]: st.dataframe(df(pf.get("return_metrics",{})), use_container_width=True, hide_index=True)
    
    with st.expander("Sensitivity"):
        s = compute_sensitivity_table(pf, target_irr=14.0)
        sdf = pd.DataFrame({"Cap": s["rows"]})
        for i,c in enumerate(s["cols"]): sdf[c] = [f"{s['values'][j][i]:.1f}%" if s['values'][j][i] else "—" for j in range(3)]
        st.dataframe(sdf, use_container_width=True, hide_index=True)
    
    c1, c2 = st.columns(2)
    sens = compute_sensitivity_table(pf, target_irr=14.0)
    exp = {**data, "sensitivity": sens}
    with c1:
        st.download_button("Download Excel", export_pro_forma(exp, name), get_suggested_filename(exp), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c2:
        st.download_button("Download JSON", json.dumps(pf, indent=2, default=str), f"{name}.json", "application/json", use_container_width=True)

# Render answer
def show_answer(txt, src, conf):
    st.markdown(txt)
    if src:
        tags = "".join(f'<span class="src-tag">{s}</span>' for s in src[:3])
        st.markdown(f'<div style="margin-top:0.5rem;">{tags}</div>', unsafe_allow_html=True)

# Sidebar - Chat History
with st.sidebar:
    st.markdown("### FAiLLON")
    st.caption("Development Intelligence")
    st.markdown("---")
    
    # New chat button
    if st.button("+ New Chat", use_container_width=True):
        if st.session_state.messages:
            first_msg = st.session_state.messages[0]["content"][:40] + "..." if len(st.session_state.messages[0]["content"]) > 40 else st.session_state.messages[0]["content"]
            st.session_state.chat_history.insert(0, {"title": first_msg, "messages": st.session_state.messages.copy()})
        st.session_state.messages = []
        st.session_state.pending = None
        st.session_state.model = None
        st.session_state.run_query = None
        st.rerun()
    
    st.markdown("---")
    st.caption("RECENT")
    
    # Show chat history
    for i, chat in enumerate(st.session_state.chat_history[:10]):
        if st.button(chat["title"], key=f"hist_{i}", use_container_width=True):
            st.session_state.messages = chat["messages"].copy()
            st.rerun()
    
    st.markdown("---")
    st.caption("DATA")
    try:
        cnt = get_collection_counts()
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Deals", cnt.get("fallon_deal_data", 0))
        with c2:
            st.metric("Research", cnt.get("fallon_market_research", 0))
    except: pass
    
    # Show learned insights
    st.markdown("---")
    st.caption("LEARNED")
    try:
        ctx = get_user_context()
        if ctx.get("has_history"):
            if ctx.get("preferred_markets"):
                markets = ", ".join([m[0].title() for m in ctx["preferred_markets"][:2]])
                st.caption(f"Markets: {markets}")
            if ctx.get("preferred_programs"):
                progs = ", ".join([p[0].title() for p in ctx["preferred_programs"][:2]])
                st.caption(f"Types: {progs}")
            if ctx.get("typical_deal_size"):
                st.caption(f"Avg Deal: ${ctx['typical_deal_size']/1e6:.0f}M")
            st.caption(f"Interactions: {ctx['interaction_count']}")
    except: pass

# Main content
if not st.session_state.messages and not st.session_state.run_query:
    st.markdown('<div class="hero"><h1>FAiLLON</h1><p>Development intelligence for real estate professionals</p></div>', unsafe_allow_html=True)
    
    # Quick action buttons
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("250 unit MF, Charlotte, 5.25 cap", use_container_width=True, key="b1"):
            st.session_state.run_query = "250 unit multifamily in Charlotte with 5.25 exit cap"
            st.rerun()
    with c2:
        if st.button("Boston Seaport cap rates", use_container_width=True, key="b2"):
            st.session_state.run_query = "What are current cap rates in Boston Seaport for multifamily?"
            st.rerun()
    with c3:
        if st.button("JV waterfall structures", use_container_width=True, key="b3"):
            st.session_state.run_query = "Explain typical JV waterfall and promote structures"
            st.rerun()

# Process button click
if st.session_state.run_query:
    query = st.session_state.run_query
    st.session_state.run_query = None
    st.session_state.messages.append({"role": "user", "content": query})
    resp = process(query)
    st.session_state.messages.append({"role": "assistant", "resp": resp})
    st.rerun()

# Display chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m["role"] == "user":
            st.markdown(m["content"])
        else:
            r = m.get("resp", {})
            if r.get("t") == "model":
                show_model(r["data"], r.get("txt"))
            elif r.get("t") == "answer":
                show_answer(r["txt"], r.get("src", []), r.get("conf", "medium"))
            elif r.get("t") == "clarify":
                st.info(r["txt"])
            else:
                st.markdown(r.get("txt", ""))

# Chat input
if prompt := st.chat_input("Message FAiLLON..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        resp = process(prompt)
        if resp.get("t") == "model":
            show_model(resp["data"], resp.get("txt"))
        elif resp.get("t") == "answer":
            show_answer(resp["txt"], resp.get("src", []), resp.get("conf", "medium"))
        elif resp.get("t") == "clarify":
            st.info(resp["txt"])
        else:
            st.markdown(resp.get("txt", ""))
        st.session_state.messages.append({"role": "assistant", "resp": resp})
