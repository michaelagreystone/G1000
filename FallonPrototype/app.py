"""
FAiLLON — Conversational Development Intelligence
"""

import streamlit as st
import pandas as pd
import json
import sys
import os
import copy
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from FallonPrototype.shared.claude_client import call_claude
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
    format_context_for_prompt
)

st.set_page_config(page_title="FAiLLON", page_icon="◼", layout="wide", initial_sidebar_state="expanded")

# Dark theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }
.stApp { background: #000000 !important; }
.main .block-container { max-width: 900px; padding: 1rem 2rem 7rem 2rem; }
h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
p, span, li, label { color: #d1d5db; }
[data-testid="stSidebar"] { background: #171717 !important; border-right: 1px solid #2a2a2a !important; }
[data-testid="stSidebar"] * { color: #d1d5db !important; }
/* Sidebar expand button - WHITE and VISIBLE */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[kind="header"],
[data-testid="baseButton-header"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    left: 5px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    background: #1a1a1a !important;
    border: 2px solid #ffffff !important;
    border-radius: 0 12px 12px 0 !important;
    border-left: none !important;
    padding: 20px 10px !important;
    z-index: 999999 !important;
    cursor: pointer !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
button[kind="header"] svg {
    width: 20px !important;
    height: 20px !important;
    fill: #ffffff !important;
    stroke: #ffffff !important;
    color: #ffffff !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: #2a2a2a !important;
}
[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.1rem !important; }
[data-testid="stMetricLabel"] { color: #6b7280 !important; font-size: 0.65rem !important; text-transform: uppercase !important; }
.stButton > button { background: #2f2f2f !important; color: #d1d5db !important; border: 1px solid #404040 !important; border-radius: 24px !important; padding: 0.6rem 1rem !important; font-size: 0.875rem !important; }
.stButton > button:hover { background: #404040 !important; color: #ffffff !important; }
.stDownloadButton > button { background: #10a37f !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; }
[data-testid="stChatMessage"] { background: transparent !important; padding: 1rem 0 !important; }
[data-testid="stChatMessageContent"] { background: transparent !important; padding: 0.5rem 0 !important; border: none !important; }
[data-testid="stChatMessageContent"] p { color: #ececec !important; font-size: 0.9375rem !important; line-height: 1.6 !important; }
/* Remove ALL backgrounds from bottom chat area - AGGRESSIVE */
.stBottom, [data-testid="stBottom"], [data-testid="stBottomBlockContainer"],
.stChatFloatingInputContainer, [data-testid="stChatFloatingInputContainer"],
[class*="stBottom"], [class*="ChatInput"], [class*="FloatingInput"],
[class*="emotion-cache"], section[data-testid="stBottom"] > div,
.block-container + div, iframe + div {
    background: #000000 !important;
    background-color: #000000 !important;
    border: none !important;
    box-shadow: none !important;
}
/* The actual input container - just the rounded input field */
[data-testid="stChatInput"], .stChatInput { 
    background: transparent !important; 
    background-color: transparent !important;
}
[data-testid="stChatInput"] > div, .stChatInput > div,
[data-testid="stChatInput"] > div > div { 
    background: #000000 !important; 
    background-color: #000000 !important;
    border: 1px solid #404040 !important; 
    border-radius: 26px !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] textarea, .stChatInput textarea { 
    color: #ffffff !important; 
    -webkit-text-fill-color: #ffffff !important; 
    background: transparent !important; 
    background-color: transparent !important;
}
[data-testid="stChatInput"] textarea::placeholder, .stChatInput textarea::placeholder { 
    color: #6b7280 !important; 
    -webkit-text-fill-color: #6b7280 !important; 
}
/* Kill any remaining backgrounds */
div[data-testid="stBottom"] * {
    background-color: transparent !important;
}
div[data-testid="stBottom"] > div:first-child {
    background: #000000 !important;
}
.metric-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1rem; text-align: center; }
.metric-value { font-size: 1.5rem; font-weight: 600; color: #ffffff; }
.metric-label { font-size: 0.6875rem; color: #6b7280; text-transform: uppercase; margin-top: 0.25rem; }
[data-testid="stDataFrame"] table { background: #1a1a1a !important; }
[data-testid="stDataFrame"] th { background: #2a2a2a !important; color: #9ca3af !important; }
[data-testid="stDataFrame"] td { background: #1a1a1a !important; color: #ececec !important; }
.streamlit-expanderHeader { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; border-radius: 8px !important; color: #ececec !important; }
.streamlit-expanderContent { background: #141414 !important; border: 1px solid #2a2a2a !important; }
.stTabs [data-baseweb="tab-list"] { background: #1a1a1a; border-radius: 8px; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #6b7280 !important; }
.stTabs [aria-selected="true"] { background: #2a2a2a !important; color: #ffffff !important; }
.stAlert { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; border-radius: 8px !important; }
.hero { text-align: center; padding: 3rem 1rem 2rem 1rem; }
.hero h1 { font-size: 2.5rem; color: #ffffff; margin-bottom: 0.5rem; }
.hero p { color: #6b7280; font-size: 1rem; }
.src-tag { display: inline-block; background: #2a2a2a; color: #9ca3af; font-size: 0.6875rem; padding: 0.2rem 0.5rem; border-radius: 4px; margin-right: 0.4rem; }
</style>
""", unsafe_allow_html=True)

# Sidebar expand button using components.html for JavaScript execution
import streamlit.components.v1 as components

components.html("""
<style>
    #expand-btn {
        position: fixed;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        background: #000000;
        border: 2px solid #ffffff;
        border-left: none;
        border-radius: 0 12px 12px 0;
        color: #ffffff;
        padding: 25px 12px;
        cursor: pointer;
        z-index: 999999;
        font-size: 18px;
        font-weight: bold;
        transition: all 0.3s ease;
        letter-spacing: -3px;
    }
    #expand-btn:hover {
        background: #1a1a1a;
        padding-left: 20px;
    }
</style>
<div id="expand-btn">▶▶</div>
<script>
    const btn = document.getElementById('expand-btn');
    const parent = window.parent.document;
    
    // Function to check if sidebar is collapsed
    function isSidebarCollapsed() {
        const sidebar = parent.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return false;
        const style = window.parent.getComputedStyle(sidebar);
        return sidebar.getAttribute('aria-expanded') === 'false' || 
               parseInt(style.width) < 50 ||
               style.transform.includes('translateX');
    }
    
    // Function to expand sidebar
    function expandSidebar() {
        // Try multiple selectors for the expand button
        const selectors = [
            '[data-testid="collapsedControl"]',
            '[data-testid="stSidebarCollapsedControl"]', 
            'button[kind="header"]',
            '[data-testid="stSidebar"] button',
            'button[aria-label="Expand sidebar"]'
        ];
        
        for (const selector of selectors) {
            const expandBtn = parent.querySelector(selector);
            if (expandBtn) {
                expandBtn.click();
                return true;
            }
        }
        
        // Fallback: directly manipulate sidebar
        const sidebar = parent.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.transition = 'all 0.3s ease';
            sidebar.style.transform = 'translateX(0)';
            sidebar.style.width = '260px';
            sidebar.setAttribute('aria-expanded', 'true');
        }
        return false;
    }
    
    // Click handler
    btn.addEventListener('click', function() {
        expandSidebar();
        btn.style.opacity = '0';
        setTimeout(() => { btn.style.display = 'none'; }, 300);
    });
    
    // Watch for sidebar state changes
    function updateVisibility() {
        if (isSidebarCollapsed()) {
            btn.style.display = 'block';
            btn.style.opacity = '1';
        } else {
            btn.style.opacity = '0';
            setTimeout(() => { 
                if (!isSidebarCollapsed()) btn.style.display = 'none'; 
            }, 300);
        }
    }
    
    // Initial check and observer
    updateVisibility();
    setInterval(updateVisibility, 500);
</script>
""", height=0)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "project_data" not in st.session_state:
    st.session_state.project_data = {}  # Accumulated project info
if "model" not in st.session_state:
    st.session_state.model = None
if "conversation_mode" not in st.session_state:
    st.session_state.conversation_mode = "chat"  # chat, gathering, refining
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATIONAL AI - Natural dialogue with Claude
# ═══════════════════════════════════════════════════════════════════════════════

CONVERSATION_PROMPT = """You are FAiLLON, a conversational AI assistant specializing in real estate development finance. You help users analyze and underwrite development projects through natural conversation.

YOUR PERSONALITY:
- Professional but friendly
- Ask clarifying questions to understand the project better
- Don't rush to generate pro formas - gather information first
- Be helpful even when users just want to chat or ask questions
- Explain concepts when asked

CURRENT PROJECT DATA (what you know so far):
{project_data}

USER'S LEARNED PREFERENCES:
{user_context}

CONVERSATION HISTORY:
{history}

CURRENT USER MESSAGE: {message}

RESPOND BASED ON WHAT THE USER NEEDS:

1. IF CASUAL CHAT or QUESTION: Just have a helpful conversation. Answer questions about real estate, explain concepts, discuss market trends.

2. IF STARTING A NEW PROJECT: Ask follow-up questions to gather key info:
   - What market/city?
   - What type of development (multifamily, office, hotel, mixed-use)?
   - What's the parcel size (acres or SF)?
   - How many units/keys/SF are they targeting?
   - Any specific return targets?
   - What's their timeline?
   
3. IF REFINING AN EXISTING MODEL: Help them adjust assumptions:
   - Understand what they want to change
   - Suggest reasonable adjustments
   - Explain impact of changes

4. IF THEY WANT TO GENERATE: Only generate when you have:
   - Market
   - Property type
   - Parcel size
   - Unit count or SF
   
RESPONSE FORMAT:
Return a JSON object with:
{{
  "response": "Your conversational response to the user",
  "intent": "chat" | "gather_info" | "generate_model" | "adjust_model" | "answer_question",
  "extracted_data": {{any new project parameters you learned}},
  "follow_up_questions": ["list of follow-up questions if gathering info"],
  "ready_to_generate": true/false
}}

Be conversational and helpful. Don't be robotic. Ask good questions to understand what they're really trying to accomplish."""


def get_ai_response(user_message: str) -> dict:
    """Get conversational response from Claude."""
    
    # Build conversation history
    history = ""
    for msg in st.session_state.messages[-10:]:  # Last 10 messages
        role = "User" if msg["role"] == "user" else "FAiLLON"
        content = msg.get("content", "")
        if isinstance(content, str):
            history += f"{role}: {content}\n"
    
    # Get user context
    user_ctx = get_user_context()
    ctx_str = format_context_for_prompt() if user_ctx.get("has_history") else "No prior history"
    
    # Format project data
    proj_data = json.dumps(st.session_state.project_data, indent=2) if st.session_state.project_data else "No project data yet"
    
    prompt = CONVERSATION_PROMPT.format(
        project_data=proj_data,
        user_context=ctx_str,
        history=history,
        message=user_message
    )
    
    try:
        response = call_claude(prompt, max_tokens=1500)
        
        # Parse JSON response
        try:
            # Find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return result
        except json.JSONDecodeError:
            pass
        
        # Fallback if not valid JSON
        return {
            "response": response,
            "intent": "chat",
            "extracted_data": {},
            "follow_up_questions": [],
            "ready_to_generate": False
        }
        
    except Exception as e:
        return {
            "response": f"I'm having trouble processing that. Could you rephrase? (Error: {str(e)[:50]})",
            "intent": "chat",
            "extracted_data": {},
            "follow_up_questions": [],
            "ready_to_generate": False
        }


def process_message(user_message: str) -> dict:
    """Process user message and return appropriate response."""
    
    # Check for explicit adjustment commands on existing model
    if st.session_state.model:
        m = user_message.lower()
        if any(k in m for k in ["change", "adjust", "set", "update", "modify", "make it", "what if"]):
            return handle_adjustment(user_message)
    
    # Get AI response
    ai_result = get_ai_response(user_message)
    
    # Update project data with any extracted info
    if ai_result.get("extracted_data"):
        st.session_state.project_data.update(ai_result["extracted_data"])
    
    # If ready to generate and user seems to want it
    if ai_result.get("ready_to_generate") and ai_result.get("intent") == "generate_model":
        return generate_model_from_data()
    
    # If answering a question about contracts/market
    if ai_result.get("intent") == "answer_question":
        # Try to get relevant context
        try:
            r = answer_contract_question(user_message)
            if r.answer and r.confidence != "low":
                return {
                    "t": "answer",
                    "txt": ai_result["response"] + "\n\n" + r.answer if ai_result["response"] else r.answer,
                    "src": r.sources,
                    "conf": r.confidence
                }
        except:
            pass
    
    # Regular conversational response
    response_text = ai_result.get("response", "I'm not sure how to help with that.")
    
    # Add follow-up questions if gathering info
    if ai_result.get("follow_up_questions"):
        questions = ai_result["follow_up_questions"]
        if questions:
            response_text += "\n\n**A few questions to help me understand better:**"
            for q in questions[:3]:
                response_text += f"\n- {q}"
    
    record_interaction(user_message, ai_result.get("intent", "chat"), "text", success=True)
    
    return {"t": "txt", "txt": response_text}


def handle_adjustment(user_message: str) -> dict:
    """Handle adjustments to existing model."""
    if not st.session_state.model:
        return {"t": "txt", "txt": "Let's create a model first. Tell me about your project."}
    
    pf = copy.deepcopy(st.session_state.model["pro_forma"])
    changes = []
    m = user_message.lower()
    
    # Extract adjustments
    if cap := re.search(r'cap\s*(?:rate)?\s*(?:to|=|:)?\s*(\d+\.?\d*)', m):
        v = float(cap.group(1))
        if "return_metrics" in pf:
            old = _val(pf["return_metrics"], "exit_cap_rate_pct")
            pf["return_metrics"]["exit_cap_rate_pct"] = {"value": v, "unit": "%", "label": "confirmed", "source": "user adjustment"}
            changes.append(f"exit cap to {v}%")
            record_adjustment("exit_cap_rate_pct", old, v, {})
    
    if rent := re.search(r'rent\s*(?:to|=|:)?\s*\$?(\d+\.?\d*)', m):
        v = float(rent.group(1))
        if "revenue_assumptions" in pf:
            old = _val(pf["revenue_assumptions"], "rent_psf_monthly")
            pf["revenue_assumptions"]["rent_psf_monthly"] = {"value": v, "unit": "$/SF/mo", "label": "confirmed", "source": "user adjustment"}
            changes.append(f"rent to ${v}/SF")
            record_adjustment("rent_psf_monthly", old, v, {})
    
    if units := re.search(r'(\d+)\s*units?', m):
        v = int(units.group(1))
        if "project_summary" in pf:
            old = _val(pf["project_summary"], "unit_count")
            pf["project_summary"]["unit_count"] = {"value": v, "unit": "units", "label": "confirmed", "source": "user adjustment"}
            changes.append(f"units to {v}")
    
    if hard := re.search(r'hard\s*(?:cost)?\s*(?:to|=|:)?\s*\$?(\d+)', m):
        v = float(hard.group(1))
        if "cost_assumptions" in pf:
            pf["cost_assumptions"]["hard_cost_psf"] = {"value": v, "unit": "$/SF", "label": "confirmed", "source": "user adjustment"}
            changes.append(f"hard cost to ${v}/SF")
    
    if changes:
        calc = compute_returns(pf)
        st.session_state.model = {
            "pro_forma": pf,
            "calc_results": calc,
            "warnings": check_return_discrepancy(pf, calc)
        }
        return {
            "t": "model",
            "data": st.session_state.model,
            "txt": f"Got it! I've updated: {', '.join(changes)}. Here's the revised model:"
        }
    
    return {"t": "txt", "txt": "I couldn't identify what you'd like to change. Try something like 'change cap rate to 5.5' or 'set rent to $2.75'."}


def generate_model_from_data() -> dict:
    """Generate model from accumulated project data."""
    data = st.session_state.project_data
    
    # Build query from accumulated data
    parts = []
    if data.get("market"):
        parts.append(data["market"])
    if data.get("program_type"):
        parts.append(data["program_type"])
    if data.get("unit_count"):
        parts.append(f"{data['unit_count']} units")
    if data.get("parcel_acres"):
        parts.append(f"{data['parcel_acres']} acres")
    if data.get("exit_cap"):
        parts.append(f"{data['exit_cap']} cap")
    
    query = " ".join(parts) if parts else "multifamily development"
    
    try:
        r = run(query, user_context=get_user_context())
        
        if r.export_data and "pro_forma" in r.export_data:
            st.session_state.model = r.export_data
            record_interaction(query, "generate", "model", pro_forma=r.export_data.get("pro_forma"), success=True)
            return {
                "t": "model",
                "data": r.export_data,
                "txt": "Here's the pro forma based on what we discussed. Feel free to ask me to adjust any assumptions!"
            }
        
        if r.needs_clarification:
            return {"t": "txt", "txt": r.answer}
        
        return {"t": "txt", "txt": r.answer}
        
    except Exception as e:
        return {"t": "txt", "txt": f"I had trouble generating the model. Let me know more details about your project."}


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def show_model(data, note=None):
    pf = data.get("pro_forma", {})
    ret = pf.get("return_metrics", {})
    cost = pf.get("cost_assumptions", {})
    name = _val(pf.get("project_summary", {}), "deal_name", "Model")
    
    if note:
        st.markdown(note)
    
    st.markdown(f"**{name}**")
    
    c1, c2, c3, c4 = st.columns(4)
    irr = _val(ret, "project_irr_levered_pct")
    mult = _val(ret, "equity_multiple_lp")
    poc = _val(ret, "profit_on_cost_pct")
    tc = _val(cost, "total_project_cost")
    
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
        for i, c in enumerate(s["cols"]):
            sdf[c] = [f"{s['values'][j][i]:.1f}%" if s['values'][j][i] else "—" for j in range(3)]
        st.dataframe(sdf, use_container_width=True, hide_index=True)
    
    c1, c2 = st.columns(2)
    sens = compute_sensitivity_table(pf, target_irr=14.0)
    exp = {**data, "sensitivity": sens}
    with c1:
        st.download_button("Download Excel", export_pro_forma(exp, name), get_suggested_filename(exp), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c2:
        st.download_button("Download JSON", json.dumps(pf, indent=2, default=str), f"{name}.json", "application/json", use_container_width=True)
    
    st.markdown("---")
    st.caption("💡 You can say things like 'change the cap rate to 5.5' or 'what if we had 200 units instead?' to adjust the model.")


def show_answer(txt, src, conf):
    st.markdown(txt)
    if src:
        tags = "".join(f'<span class="src-tag">{s}</span>' for s in src[:3])
        st.markdown(f'<div style="margin-top:0.5rem;">{tags}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### FAiLLON")
    st.caption("Development Intelligence")
    st.markdown("---")
    
    if st.button("+ New Conversation", use_container_width=True):
        if st.session_state.messages:
            first_msg = st.session_state.messages[0].get("content", "")[:40]
            st.session_state.chat_history.insert(0, {
                "title": first_msg + "..." if len(first_msg) >= 40 else first_msg,
                "messages": st.session_state.messages.copy(),
                "project_data": st.session_state.project_data.copy()
            })
        st.session_state.messages = []
        st.session_state.project_data = {}
        st.session_state.model = None
        st.rerun()
    
    st.markdown("---")
    st.caption("RECENT")
    for i, chat in enumerate(st.session_state.chat_history[:8]):
        if st.button(chat.get("title", "Chat"), key=f"hist_{i}", use_container_width=True):
            st.session_state.messages = chat.get("messages", []).copy()
            st.session_state.project_data = chat.get("project_data", {}).copy()
            st.session_state.model = None
            st.rerun()
    
    st.markdown("---")
    st.caption("PROJECT DATA")
    if st.session_state.project_data:
        for k, v in list(st.session_state.project_data.items())[:6]:
            st.caption(f"{k}: {v}")
    else:
        st.caption("No project started")
    
    st.markdown("---")
    try:
        cnt = get_collection_counts()
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Deals", cnt.get("fallon_deal_data", 0))
        with c2:
            st.metric("Research", cnt.get("fallon_market_research", 0))
    except:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

# Hero when empty
if not st.session_state.messages:
    st.markdown('<div class="hero"><h1>FAiLLON</h1><p>Let\'s talk about your development project</p></div>', unsafe_allow_html=True)
    
    st.markdown("**I can help you with:**")
    st.markdown("- Underwriting and pro forma analysis")
    st.markdown("- Market research and cap rate trends")
    st.markdown("- JV structures and waterfalls")
    st.markdown("- Contract terms and provisions")
    st.markdown("")
    st.markdown("Just tell me about what you're working on, or ask me anything about real estate development.")

# Display chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m["role"] == "user":
            st.markdown(m.get("content", ""))
        else:
            r = m.get("resp", {})
            if r.get("t") == "model":
                show_model(r["data"], r.get("txt"))
            elif r.get("t") == "answer":
                show_answer(r["txt"], r.get("src", []), r.get("conf", "medium"))
            else:
                st.markdown(r.get("txt", m.get("content", "")))

# Chat input
if prompt := st.chat_input("Tell me about your project, or ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            resp = process_message(prompt)
        
        if resp.get("t") == "model":
            show_model(resp["data"], resp.get("txt"))
        elif resp.get("t") == "answer":
            show_answer(resp["txt"], resp.get("src", []), resp.get("conf", "medium"))
        else:
            st.markdown(resp.get("txt", ""))
        
        st.session_state.messages.append({"role": "assistant", "resp": resp})
