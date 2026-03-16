"""
AI Contract Reviewer — Demo Day Tool
Upload any contract PDF and get an instant plain-English breakdown.
"""

import streamlit as st
from shared.document_parser import parse_uploaded_file
from shared.contract_reviewer import ingest_contract, generate_review, ask_question
from shared.vector_store import get_count

# -- Page Config ---------------------------------------------------------------

st.set_page_config(
    page_title="AI Contract Reviewer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -- Premium Dark + Liquid Glass CSS ------------------------------------------

st.markdown("""
<style>
/* ── Reset Streamlit defaults ─────────────────────────────────────────────── */
.stApp {
    background: #0a0a0f !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}
.block-container {
    padding-top: 2rem !important;
    max-width: 1100px !important;
}

/* ── Animated Liquid Background ───────────────────────────────────────────── */
.liquid-bg {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    z-index: 0;
    overflow: hidden;
    pointer-events: none;
}
.blob {
    position: absolute;
    border-radius: 50%;
    filter: blur(120px);
    opacity: 0.3;
}
.blob-1 {
    width: 600px; height: 600px;
    background: #1e1b4b;
    top: -10%; left: -5%;
    animation: drift1 20s ease-in-out infinite;
}
.blob-2 {
    width: 500px; height: 500px;
    background: #4c1d95;
    bottom: -10%; right: -5%;
    animation: drift2 25s ease-in-out infinite;
}
.blob-3 {
    width: 400px; height: 400px;
    background: #1e3a5f;
    top: 30%; left: 50%;
    animation: drift3 30s ease-in-out infinite;
}
@keyframes drift1 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    50%      { transform: translate(30vw, 20vh) scale(1.1); }
}
@keyframes drift2 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    50%      { transform: translate(-25vw, -15vh) scale(1.15); }
}
@keyframes drift3 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    50%      { transform: translate(-20vw, -25vh) scale(0.9); }
}

/* ── Glass Card ───────────────────────────────────────────────────────────── */
.glass {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 20px;
    position: relative;
    z-index: 1;
}
.glass-sm {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    position: relative;
    z-index: 1;
}

/* ── Accent border variant ────────────────────────────────────────────────── */
.glass-accent {
    border-left: 3px solid;
    border-image: linear-gradient(180deg, #6366f1, #8b5cf6) 1;
}

/* ── Hero Section ─────────────────────────────────────────────────────────── */
.hero {
    text-align: center;
    padding: 60px 20px 20px;
    position: relative;
    z-index: 1;
}
.hero h1 {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #c7d2fe 0%, #a78bfa 50%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.hero p {
    color: #64748b;
    font-size: 1.15rem;
    margin-top: 0;
}

/* ── Upload Zone ──────────────────────────────────────────────────────────── */
.upload-zone {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 2px dashed rgba(99,102,241,0.3);
    border-radius: 16px;
    padding: 48px 32px;
    text-align: center;
    transition: border-color 0.3s, box-shadow 0.3s;
    position: relative;
    z-index: 1;
}
.upload-zone:hover {
    border-color: rgba(99,102,241,0.6);
    box-shadow: 0 0 30px rgba(99,102,241,0.15);
}
.upload-zone h3 {
    color: #e2e8f0;
    margin-bottom: 8px;
}
.upload-zone p {
    color: #64748b;
    font-size: 0.95rem;
}

/* ── Format pills ─────────────────────────────────────────────────────────── */
.format-pills {
    display: flex;
    gap: 8px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 16px;
}
.pill {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.8rem;
    color: #94a3b8;
}

/* ── Top Stats Strip ──────────────────────────────────────────────────────── */
.top-strip {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 14px 28px;
    display: flex;
    align-items: center;
    gap: 28px;
    margin-bottom: 24px;
    position: relative;
    z-index: 1;
}
.top-strip .strip-item {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #94a3b8;
    font-size: 0.9rem;
}
.top-strip .strip-item strong {
    color: #e2e8f0;
}
.strip-divider {
    width: 1px;
    height: 20px;
    background: rgba(255,255,255,0.1);
}

/* ── Section Header ───────────────────────────────────────────────────────── */
.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #c7d2fe;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title .icon {
    font-size: 1.2rem;
}

/* ── Risk Cards ───────────────────────────────────────────────────────────── */
.risk-card {
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    border: 1px solid rgba(255,255,255,0.06);
}
.risk-high {
    background: rgba(239, 68, 68, 0.08);
    border-left: 3px solid #ef4444;
}
.risk-medium {
    background: rgba(245, 158, 11, 0.08);
    border-left: 3px solid #f59e0b;
}
.risk-low {
    background: rgba(34, 197, 94, 0.08);
    border-left: 3px solid #22c55e;
}
.risk-card .risk-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}
.risk-high .risk-label { color: #ef4444; }
.risk-medium .risk-label { color: #f59e0b; }
.risk-low .risk-label { color: #22c55e; }
.risk-card .risk-text {
    color: #cbd5e1;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* ── Chat Bubbles ─────────────────────────────────────────────────────────── */
.chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 12px 0;
}
.chat-bubble {
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 12px;
    max-width: 85%;
    line-height: 1.5;
    font-size: 0.95rem;
}
.chat-user {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    margin-left: auto;
    border-bottom-right-radius: 4px;
}
.chat-assistant {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    color: #e2e8f0;
    border-bottom-left-radius: 4px;
}

/* ── Key Terms Grid ───────────────────────────────────────────────────────── */
.terms-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
@media (max-width: 640px) {
    .terms-grid { grid-template-columns: 1fr; }
}
.term-item {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 14px 16px;
}
.term-item .term-label {
    font-size: 0.8rem;
    color: #64748b;
    margin-bottom: 4px;
}
.term-item .term-value {
    color: #e2e8f0;
    font-size: 0.95rem;
}

/* ── Security text ────────────────────────────────────────────────────────── */
.security-muted {
    text-align: center;
    color: #475569;
    font-size: 0.82rem;
    margin-top: 28px;
    position: relative;
    z-index: 1;
}

/* ── Sidebar Glass ────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: rgba(10,10,15,0.85) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #c7d2fe;
}

/* ── Streamlit element overrides ──────────────────────────────────────────── */
.stTextArea textarea {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #cbd5e1 !important;
}
.stChatMessage {
    background: transparent !important;
}
.stExpander {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
}
button[data-testid="stBaseButton-secondary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    color: white !important;
    border-radius: 10px !important;
}
div[data-testid="stFileUploader"] {
    background: transparent !important;
}
div[data-testid="stFileUploader"] section {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
}
</style>

<!-- Liquid animated background -->
<div class="liquid-bg">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
</div>
""", unsafe_allow_html=True)

# -- Session State -------------------------------------------------------------

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

# -- Landing Page (no contract uploaded) ---------------------------------------

if st.session_state.contract_text is None:

    st.markdown("""
    <div class="hero">
        <h1>AI Contract Reviewer</h1>
        <p>Upload any contract and get an instant plain-English breakdown</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="upload-zone">
            <h3>Drop your contract here</h3>
            <p>We'll analyze it in seconds with AI</p>
            <div class="format-pills">
                <span class="pill">PDF</span>
                <span class="pill">DOCX</span>
                <span class="pill">TXT</span>
                <span class="pill">PNG</span>
                <span class="pill">JPG</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

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

                with st.spinner("Generating AI review..."):
                    review = generate_review(text)
                    st.session_state.review_result = review

                st.rerun()

    st.markdown("""
    <div class="security-muted">
        🔒 Your documents are processed locally and never stored. They're deleted when you close this tab.
    </div>
    """, unsafe_allow_html=True)

else:
    # -- Review Page -----------------------------------------------------------

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="glass-sm" style="margin-top: 12px;">
            <div class="section-title"><span class="icon">📋</span> Contract Info</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"**File:** {st.session_state.filename}")
        st.markdown(f"**Characters:** {len(st.session_state.contract_text):,}")
        st.markdown(f"**Chunks indexed:** {st.session_state.chunk_count}")
        st.markdown("---")
        if st.button("New Contract", use_container_width=True):
            st.session_state.contract_text = None
            st.session_state.review_result = None
            st.session_state.filename = None
            st.session_state.chat_history = []
            st.session_state.chunk_count = 0
            st.rerun()

    # Top stats strip
    text_len = len(st.session_state.contract_text)
    st.markdown(f"""
    <div class="top-strip">
        <div class="strip-item">
            <span>📄</span>
            <strong>{st.session_state.filename}</strong>
        </div>
        <div class="strip-divider"></div>
        <div class="strip-item">
            <span>{text_len:,}</span> characters
        </div>
        <div class="strip-divider"></div>
        <div class="strip-item">
            <span>{st.session_state.chunk_count}</span> chunks indexed
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -- Review Content (single scrollable page) -------------------------------

    if st.session_state.review_result:
        if st.session_state.review_result.startswith("ERROR:"):
            st.error(st.session_state.review_result)
        else:
            review = st.session_state.review_result

            # Parse review into sections
            # The review is markdown — render each major section in its own glass card
            sections = review.split("\n## ")
            intro = sections[0] if sections else ""

            # Summary card
            st.markdown(f"""
            <div class="glass glass-accent">
                <div class="section-title"><span class="icon">📊</span> Review Summary</div>
                <div style="color: #cbd5e1; line-height: 1.7;">
            """, unsafe_allow_html=True)
            # Render the intro / first block
            if intro.strip():
                st.markdown(intro)
            st.markdown("</div></div>", unsafe_allow_html=True)

            # Remaining sections in glass cards
            for section in sections[1:]:
                heading_end = section.find("\n")
                if heading_end == -1:
                    heading = section.strip()
                    body = ""
                else:
                    heading = section[:heading_end].strip()
                    body = section[heading_end:].strip()

                # Detect risk-related sections
                heading_lower = heading.lower()
                card_class = "glass"
                if "risk" in heading_lower or "flag" in heading_lower or "concern" in heading_lower:
                    card_class = "glass"
                    # Render risk items specially if body contains risk markers
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div class="section-title"><span class="icon">⚠️</span> {heading}</div>
                    """, unsafe_allow_html=True)
                    # Parse risk items from body
                    if body.strip():
                        _render_risks = True
                        lines = body.split("\n")
                        for line in lines:
                            line_stripped = line.strip()
                            if not line_stripped:
                                continue
                            line_lower = line_stripped.lower()
                            if "high" in line_lower and ("risk" in line_lower or "🔴" in line_stripped or "**high" in line_lower):
                                st.markdown(f"""<div class="risk-card risk-high">
                                    <div class="risk-label">High Risk</div>
                                    <div class="risk-text">{line_stripped}</div>
                                </div>""", unsafe_allow_html=True)
                            elif "medium" in line_lower and ("risk" in line_lower or "🟡" in line_stripped or "**medium" in line_lower):
                                st.markdown(f"""<div class="risk-card risk-medium">
                                    <div class="risk-label">Medium Risk</div>
                                    <div class="risk-text">{line_stripped}</div>
                                </div>""", unsafe_allow_html=True)
                            elif "low" in line_lower and ("risk" in line_lower or "🟢" in line_stripped or "**low" in line_lower):
                                st.markdown(f"""<div class="risk-card risk-low">
                                    <div class="risk-label">Low Risk</div>
                                    <div class="risk-text">{line_stripped}</div>
                                </div>""", unsafe_allow_html=True)
                            else:
                                st.markdown(line_stripped)
                    st.markdown("</div>", unsafe_allow_html=True)

                elif "key term" in heading_lower or "terms" in heading_lower:
                    icon = "📝"
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div class="section-title"><span class="icon">{icon}</span> {heading}</div>
                    """, unsafe_allow_html=True)
                    if body.strip():
                        st.markdown(body)
                    st.markdown("</div>", unsafe_allow_html=True)

                elif "deadline" in heading_lower or "date" in heading_lower or "timeline" in heading_lower:
                    icon = "📅"
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div class="section-title"><span class="icon">{icon}</span> {heading}</div>
                    """, unsafe_allow_html=True)
                    if body.strip():
                        st.markdown(body)
                    st.markdown("</div>", unsafe_allow_html=True)

                elif "money" in heading_lower or "financial" in heading_lower or "payment" in heading_lower or "compensation" in heading_lower:
                    icon = "💰"
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div class="section-title"><span class="icon">{icon}</span> {heading}</div>
                    """, unsafe_allow_html=True)
                    if body.strip():
                        st.markdown(body)
                    st.markdown("</div>", unsafe_allow_html=True)

                else:
                    icon = "📌"
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div class="section-title"><span class="icon">{icon}</span> {heading}</div>
                    """, unsafe_allow_html=True)
                    if body.strip():
                        st.markdown(body)
                    st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("Review is being generated...")

    # -- Q&A Chat Section ------------------------------------------------------

    st.markdown("""
    <div class="glass">
        <div class="section-title"><span class="icon">💬</span> Ask Questions About Your Contract</div>
        <p style="color: #64748b; font-size: 0.9rem; margin-top: 0;">
            Ask anything — <em>Can I terminate early? What happens if I miss a payment? Is there a non-compete?</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Display chat history with styled bubbles
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble chat-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask a question about your contract..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.markdown(f'<div class="chat-bubble chat-user">{prompt}</div>', unsafe_allow_html=True)

        with st.spinner("Searching contract..."):
            answer = ask_question(prompt)

        st.markdown(f'<div class="chat-bubble chat-assistant">{answer}</div>', unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

    # -- Raw Text Expander -----------------------------------------------------

    with st.expander("📄 Raw Extracted Text"):
        st.text_area(
            "Extracted Text",
            st.session_state.contract_text,
            height=400,
            disabled=True,
            label_visibility="collapsed",
        )
