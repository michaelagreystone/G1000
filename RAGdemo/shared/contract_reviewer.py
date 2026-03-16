"""
Contract Reviewer RAG pipeline.
Handles: ingest (chunk + embed) → review (structured summary) → Q&A (RAG chat).
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .llm_client import call_llm
from .vector_store import reset_collection, add_documents, query

# ── Chunking ──────────────────────────────────────────────────────────────────

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def ingest_contract(text: str, filename: str = "contract") -> int:
    """Chunk the contract text and embed into the session vector store.
    Resets any previously stored contract first.
    Returns the number of chunks created."""
    reset_collection()
    chunks = _splitter.split_text(text)

    texts = []
    metadatas = []
    ids = []
    for i, chunk in enumerate(chunks):
        texts.append(chunk)
        metadatas.append({"source": filename, "chunk_index": i})
        ids.append(f"{filename}_{i:04d}")

    return add_documents(texts, metadatas, ids)


# ── Review Summary ────────────────────────────────────────────────────────────

REVIEW_SYSTEM_PROMPT = """You are an expert contract reviewer helping small business owners understand legal agreements in plain English. You are thorough, accurate, and practical.

When reviewing a contract, produce a structured analysis with these exact sections:

## Plain-English Summary
2-3 sentences explaining what this contract is and what it means for the reader.

## Key Terms
- **Parties**: Who is involved
- **Effective Date**: When it starts
- **Termination Date**: When it ends
- **Contract Type**: What kind of agreement this is
- **Total Value**: Dollar amounts if applicable

## Risk Flags
List any concerning clauses. For each, explain WHY it's a risk in plain English. Look for:
- Auto-renewal clauses
- Penalty clauses
- Liability shifts or indemnification
- Non-compete or non-solicitation
- Unilateral amendment rights
- Waiver of jury trial
- Unlimited liability
- Assignment restrictions
If none found, say "No significant risk flags identified."

## Important Deadlines
List all dates, notice periods, renewal windows, and payment schedules found in the contract. If none, say "No specific deadlines found."

## Money Terms
List all financial terms: total amount, payment schedule, late fees, penalties, interest rates, deposits, escrow. If none, say "No financial terms found."

CRITICAL: Base your analysis ONLY on the contract text provided. Do not make up terms that aren't in the document. If a section has no relevant information, say so clearly."""


def generate_review(contract_text: str) -> str:
    """Generate a structured review of the full contract text."""
    # Truncate very long contracts to fit in context
    max_chars = 30000
    if len(contract_text) > max_chars:
        text_to_review = contract_text[:max_chars] + f"\n\n[...truncated at {max_chars} characters. {len(contract_text) - max_chars} characters omitted.]"
    else:
        text_to_review = contract_text

    user_message = f"""Please review the following contract and provide a structured analysis:

---CONTRACT TEXT---
{text_to_review}
---END CONTRACT---"""

    return call_llm(REVIEW_SYSTEM_PROMPT, user_message, max_tokens=4096)


# ── Q&A Chat ──────────────────────────────────────────────────────────────────

QA_SYSTEM_PROMPT = """You are an expert contract reviewer helping a small business owner understand their contract. Answer questions based on the contract excerpts provided.

Rules:
1. Base your answer ONLY on the contract excerpts provided. If the answer isn't in the excerpts, say so.
2. Use plain English — avoid legal jargon unless quoting the contract directly.
3. When quoting the contract, use quotation marks and mention which section it's from if visible.
4. Be specific: cite exact numbers, dates, and terms from the contract.
5. If a question can't be fully answered from the excerpts, explain what's missing and suggest what to look for."""


def ask_question(question: str) -> str:
    """RAG-powered Q&A: retrieve relevant chunks and answer the question."""
    chunks = query(question, n_results=6)

    if not chunks:
        return "No contract has been uploaded yet. Please upload a contract first."

    # Format context
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk["metadata"].get("source", "contract")
        context_parts.append(f"[Excerpt {i} from {source}]\n{chunk['text']}")

    context = "\n\n---\n\n".join(context_parts)

    user_message = f"""QUESTION: {question}

RELEVANT CONTRACT EXCERPTS:
{context}

Please answer the question based on these excerpts from the uploaded contract."""

    return call_llm(QA_SYSTEM_PROMPT, user_message, max_tokens=2048)
