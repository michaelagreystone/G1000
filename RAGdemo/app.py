"""
AI Contract Reviewer — Demo Day Tool
Upload any contract PDF and get an instant plain-English breakdown.
"""

import streamlit as st
from shared.document_parser import parse_uploaded_file
from shared.contract_reviewer import ingest_contract, generate_review, ask_question
from shared.vector_store import get_count

# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Contract Reviewer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Security banner */
    .security-banner {
        background: linear-gradient(135deg, #1a3a2a 0%, #0d2818 100%);
        border: 1px solid #2d6a4f;
        border-radius: 8px;
        padding: 12px 20px;
        margin-bottom: 20px;
        text-align: center;
        font-size: 0.9em;
        color: #95d5b2;
    }
    .security-banner strong { color: #b7e4c7; }

    /* Risk flag colors */
    .risk-high {
        background: rgba(220, 53, 69, 0.15);
        border-left: 4px solid #dc3545;
        padding: 10px 15px;
        border-radius: 4px;
        margin: 8px 0;
    }
    .risk-medium {
        background: rgba(255, 193, 7, 0.15);
        border-left: 4px solid #ffc107;
        padding: 10px 15px;
        border-radius: 4px;
        margin: 8px 0;
    }

    /* Upload area */
    .upload-area {
        border: 2px dashed #4a5568;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        margin: 20px 0;
    }

    /* Stats row */
    .stats-row {
        display: flex;
        gap: 15px;
        margin: 15px 0;
    }
    .stat-card {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 12px 18px;
        flex: 1;
        text-align: center;
    }
    .stat-card .label { font-size: 0.8em; color: #a0aec0; }
    .stat-card .value { font-size: 1.3em; font-weight: bold; color: #e2e8f0; }

    /* Header */
    .app-header {
        text-align: center;
        padding: 20px 0 10px 0;
    }
    .app-header h1 { margin-bottom: 5px; }
    .app-header p { color: #a0aec0; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────

if "contract_text" not in st.session_state:
    st.session_state.contract_text = None
if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "filename" not in st.session_state:
    st.session_state.filename = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0

# ── Security Banner ──────────────────────────────────────────────────────────

st.markdown("""
<div class="security-banner">
    🔒 <strong>Your documents are processed locally and are never stored.</strong>
    They are deleted when you close this tab.
</div>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <h1>📋 AI Contract Reviewer</h1>
    <p>Upload any contract and get an instant plain-English breakdown</p>
</div>
""", unsafe_allow_html=True)

# ── Upload Section ────────────────────────────────────────────────────────────

if st.session_state.contract_text is None:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Upload Your Contract")
        st.markdown("Supported formats: **PDF**, **DOCX**, **TXT**, **Images** (PNG, JPG)")

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "tiff", "bmp", "webp"],
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            with st.spinner("Parsing document..."):
                text = parse_uploaded_file(uploaded_file)

            if text.startswith("[") and text.endswith("]"):
                st.error(text)
            else:
                st.session_state.contract_text = text
                st.session_state.filename = uploaded_file.name

                with st.spinner("Indexing contract for Q&A..."):
                    chunks = ingest_contract(text, uploaded_file.name)
                    st.session_state.chunk_count = chunks

                with st.spinner("Generating AI review — this may take a moment..."):
                    review = generate_review(text)
                    st.session_state.review_result = review

                st.rerun()

else:
    # ── Review Display ────────────────────────────────────────────────────────

    # Sidebar with contract info
    with st.sidebar:
        st.markdown("### Contract Info")
        st.markdown(f"**File:** {st.session_state.filename}")
        st.markdown(f"**Characters:** {len(st.session_state.contract_text):,}")
        st.markdown(f"**Chunks indexed:** {st.session_state.chunk_count}")
        st.markdown("---")
        if st.button("Upload New Contract", use_container_width=True):
            st.session_state.contract_text = None
            st.session_state.review_result = None
            st.session_state.filename = None
            st.session_state.chat_history = []
            st.session_state.chunk_count = 0
            st.rerun()

    # Stats row
    text_len = len(st.session_state.contract_text)
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-card">
            <div class="label">Document</div>
            <div class="value">{st.session_state.filename}</div>
        </div>
        <div class="stat-card">
            <div class="label">Length</div>
            <div class="value">{text_len:,} chars</div>
        </div>
        <div class="stat-card">
            <div class="label">Indexed Chunks</div>
            <div class="value">{st.session_state.chunk_count}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Review tabs
    tab_review, tab_chat, tab_raw = st.tabs(["📊 Review Summary", "💬 Ask Questions", "📄 Raw Text"])

    with tab_review:
        if st.session_state.review_result:
            if st.session_state.review_result.startswith("ERROR:"):
                st.error(st.session_state.review_result)
            else:
                st.markdown(st.session_state.review_result)
        else:
            st.info("Review is being generated...")

    with tab_chat:
        st.markdown("### Ask Questions About Your Contract")
        st.markdown("Ask anything — *Can I terminate early? What happens if I miss a payment? Is there a non-compete?*")

        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("Ask a question about your contract..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Searching contract and generating answer..."):
                    answer = ask_question(prompt)
                st.markdown(answer)

            st.session_state.chat_history.append({"role": "assistant", "content": answer})

    with tab_raw:
        st.text_area(
            "Extracted Text",
            st.session_state.contract_text,
            height=500,
            disabled=True,
            label_visibility="collapsed",
        )
