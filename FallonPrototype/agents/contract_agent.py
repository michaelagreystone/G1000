"""
Contract Q&A Agent — Answers questions about RE contracts, JV structures, and deal terms.

Uses RAG to retrieve relevant contract provisions and deal precedents,
then generates accurate answers grounded in Fallon's actual documents.
"""

import sys
import os
from dataclasses import dataclass

_AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROTO_DIR = os.path.dirname(_AGENTS_DIR)
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from FallonPrototype.shared.claude_client import call_claude
from FallonPrototype.shared.vector_store import (
    query_collection,
    DEAL_DATA_COLLECTION,
    MARKET_RESEARCH_COLLECTION,
    MARKET_DEFAULTS_COLLECTION,
    CONTRACTS_COLLECTION,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Response Structure
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ContractResponse:
    """Structured response from contract agent."""
    answer: str
    sources: list[str]
    chunks_used: list[dict]
    confidence: str  # "high" | "medium" | "low"


# ═══════════════════════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════════════════════

CONTRACT_SYSTEM_PROMPT = """You are a real estate expert for The Fallon Company, a merchant developer operating in Boston, Charlotte, and Nashville with a $6B development pipeline. Your role is to answer questions about:

OPERATING MARKETS (Boston, Charlotte, Nashville):
- Market conditions, trends, and outlooks
- Rent levels, cap rates, and pricing
- Construction costs and labor markets
- Neighborhood/submarket specifics (Seaport, South End, Gulch, etc.)
- Supply/demand dynamics

CONTRACTS & DEAL STRUCTURES:
- Joint venture (JV) agreements and LP/GP structures
- Waterfall distributions and promote structures
- Construction contracts and provisions
- Commercial lease terms
- Land purchase agreements
- Mezzanine and preferred equity structures
- Development deal terms and precedents

CRITICAL RULES:

1. GROUNDING: Base your answers on the context provided. If the context contains relevant market data, cite specific numbers. If no relevant context, say "Based on our market data..." and provide general guidance.

2. ACCURACY: When discussing specific terms (percentages, cap rates, rents, costs), cite exact values from the context. Don't make up numbers.

3. SOURCES: Reference which document your answer comes from when possible.

4. OPERATING REGION FOCUS: For questions about Boston, Charlotte, or Nashville, prioritize data from our market research and deal history in those markets.

5. PRACTICAL FOCUS: Frame answers in terms of how they apply to real estate development deals. Use examples when helpful.

6. CAVEATS: If the question involves legal advice, remind the user to consult with legal counsel.

Format your response clearly with:
- Direct answer to the question
- Supporting details from the context
- Any relevant caveats or considerations
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Query Building
# ═══════════════════════════════════════════════════════════════════════════════

def build_contract_query(question: str) -> str:
    """
    Enhance the user's question with relevant keywords for better retrieval.
    """
    topic_keywords = {
        # Contract topics
        "waterfall": "waterfall distribution promote LP GP tier hurdle preferred return",
        "promote": "promote carried interest GP incentive waterfall tier",
        "preferred": "preferred return cumulative compounded LP investor",
        "jv": "joint venture LP GP operating member investor member equity",
        "lease": "lease NNN gross rent term renewal option tenant landlord",
        "construction": "construction GMP cost-plus lump sum contractor owner hard cost",
        "land": "land purchase earnest money due diligence closing contingency",
        "mezz": "mezzanine preferred equity subordinate senior lender",
        "equity": "equity contribution capital call LP GP investor",
        "default": "default cure remedy termination breach",
        "distribution": "distribution cash flow operating capital event",
        # Market topics
        "boston": "boston seaport south boston fanpier massachusetts market rent cap rate",
        "charlotte": "charlotte south end uptown north carolina market rent cap rate",
        "nashville": "nashville gulch downtown tennessee market rent cap rate hotel",
        "rent": "rent asking rent effective rent psf monthly annual market",
        "cap rate": "cap rate exit cap capitalization rate yield",
        "cost": "construction cost hard cost soft cost psf labor materials",
        "multifamily": "multifamily apartment residential units rent occupancy",
        "office": "office commercial class a nnn rent ti allowance",
        "hotel": "hotel hospitality adr revpar occupancy keys",
        "market": "market conditions trends outlook supply demand absorption",
    }
    
    query = question.lower()
    
    for topic, keywords in topic_keywords.items():
        if topic in query:
            return f"{question} {keywords}"
    
    return question


def retrieve_contract_context(question: str, n_results: int = 8) -> list[dict]:
    """
    Retrieve relevant context from ALL knowledge bases:
    - Contracts (full contract documents with structured extraction)
    - Deal data (historical deals, contract provisions)
    - Market research (market conditions, trends, outlooks)
    - Market defaults (structured assumptions)
    """
    query = build_contract_query(question)
    all_results = []
    
    # 1. Query contracts collection (full contract documents)
    contracts_results = query_collection(
        CONTRACTS_COLLECTION,
        query,
        n_results=4,
    )
    all_results.extend(contracts_results)
    
    # 2. Query deal data collection (deals + contract provisions)
    deal_results = query_collection(
        DEAL_DATA_COLLECTION,
        query,
        n_results=4,
    )
    all_results.extend(deal_results)
    
    # 3. Query market research collection
    research_results = query_collection(
        MARKET_RESEARCH_COLLECTION,
        query,
        n_results=3,
    )
    all_results.extend(research_results)
    
    # 4. Query market defaults for structured data
    defaults_results = query_collection(
        MARKET_DEFAULTS_COLLECTION,
        query,
        n_results=2,
    )
    all_results.extend(defaults_results)
    
    # 5. Try filtered query for contract-specific docs in deal data
    contract_provision_results = query_collection(
        DEAL_DATA_COLLECTION,
        query,
        n_results=2,
        where={"doc_type": {"$eq": "contract_provision"}},
    )
    all_results.extend(contract_provision_results)
    
    # Merge and deduplicate
    seen = set()
    merged = []
    
    for result in all_results:
        text_key = result.get("text", "")[:100]
        if text_key not in seen:
            seen.add(text_key)
            merged.append(result)
    
    # Sort by relevance (distance) and return top results
    merged.sort(key=lambda r: r.get("distance", 1.0))
    return merged[:n_results]


def format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into context for the LLM."""
    if not chunks:
        return "No relevant documents found in the knowledge base."
    
    sections = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", "Unknown")
        doc_type = chunk.get("metadata", {}).get("doc_type", "document")
        relevance = chunk.get("relevance", "medium")
        text = chunk.get("text", "")
        
        sections.append(f"""
--- Document {i} ---
Source: {source}
Type: {doc_type}
Relevance: {relevance}

{text}
""")
    
    return "\n".join(sections)


# ═══════════════════════════════════════════════════════════════════════════════
# Main Query Function
# ═══════════════════════════════════════════════════════════════════════════════

def answer_contract_question(question: str) -> ContractResponse:
    """
    Answer a question about contracts, JV structures, or deal terms.
    
    Args:
        question: User's question about contracts or deal terms.
    
    Returns:
        ContractResponse with answer, sources, and confidence level.
    """
    # Retrieve relevant context
    chunks = retrieve_contract_context(question)
    context = format_context(chunks)
    
    # Build the prompt
    user_message = f"""QUESTION: {question}

RELEVANT DOCUMENTS:
{context}

Please answer the question based on the documents above. If the documents don't contain relevant information, indicate that and provide general guidance."""
    
    # Call the LLM
    response = call_claude(CONTRACT_SYSTEM_PROMPT, user_message, max_tokens=1500)
    
    if response.startswith("ERROR:"):
        return ContractResponse(
            answer=f"Unable to generate response: {response}",
            sources=[],
            chunks_used=[],
            confidence="low",
        )
    
    # Determine confidence based on retrieval quality
    high_relevance = sum(1 for c in chunks if c.get("relevance") == "high")
    medium_relevance = sum(1 for c in chunks if c.get("relevance") == "medium")
    
    if high_relevance >= 2:
        confidence = "high"
    elif high_relevance >= 1 or medium_relevance >= 2:
        confidence = "medium"
    else:
        confidence = "low"
    
    # Extract sources
    sources = list(set(
        c.get("metadata", {}).get("source", "Unknown")
        for c in chunks
        if c.get("relevance") in ("high", "medium")
    ))
    
    return ContractResponse(
        answer=response,
        sources=sources,
        chunks_used=chunks,
        confidence=confidence,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Specialized Query Functions
# ═══════════════════════════════════════════════════════════════════════════════

def explain_waterfall_structure(scenario: str = None) -> ContractResponse:
    """Explain waterfall distribution mechanics."""
    question = "How does a typical real estate JV waterfall distribution work? Explain the tiers, preferred return, catch-up, and promote structure."
    if scenario:
        question = f"Explain waterfall distribution for this scenario: {scenario}"
    return answer_contract_question(question)


def get_market_terms(term_type: str) -> ContractResponse:
    """Get current market standard terms for a specific provision type."""
    question = f"What are the typical market terms for {term_type} in real estate development deals?"
    return answer_contract_question(question)


def compare_structures(structure_a: str, structure_b: str) -> ContractResponse:
    """Compare two deal structures or provision types."""
    question = f"Compare {structure_a} vs {structure_b} in real estate deals. What are the key differences, pros, and cons?"
    return answer_contract_question(question)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI for Testing
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Interactive CLI for testing the contract agent."""
    print("=" * 60)
    print("FALLON CONTRACT Q&A AGENT")
    print("=" * 60)
    print("Ask questions about contracts, JV structures, and deal terms.")
    print("Type 'quit' to exit.\n")
    
    while True:
        question = input("\nYour question: ").strip()
        
        if question.lower() in ("quit", "exit", "q"):
            break
        
        if not question:
            continue
        
        print("\nSearching documents...")
        response = answer_contract_question(question)
        
        print(f"\n{'─' * 60}")
        print(f"Confidence: {response.confidence.upper()}")
        print(f"Sources: {', '.join(response.sources) if response.sources else 'None'}")
        print(f"{'─' * 60}")
        print(f"\n{response.answer}")
        print(f"\n{'─' * 60}")


if __name__ == "__main__":
    main()
