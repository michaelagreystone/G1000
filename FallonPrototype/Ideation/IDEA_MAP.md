# Fallon Company — Prototype Idea Map & Workflow Analysis

> Mapped from: Feb 17 transcript (Danny), Follow-Up Email (Michael Greystone)
> Purpose: Pre-build planning — what to prototype, what order, and why

---

## The Core Problem (One Sentence)

Fallon is an 18-person team managing a $6B pipeline. Their edge is judgment and speed of business plan adaptation — but the infrastructure that feeds information between verticals (investments → development → construction) is slow, manual, and disconnected. Every tool we build has to serve that core thesis: **get the right information to the right person faster.**

---

## The Four Pain Points Danny Named (Ranked by Impact)

| # | Pain Point | Danny's Words | Impact Level |
|---|-----------|---------------|--------------|
| 1 | **Contract negotiation** | "Hundreds of pages, millions in legal bills... it'd be nice if AI could do that" | Highest (direct cost) |
| 2 | **Financial modeling** | "100+ input variables... come up with a model from scratch" | High (every deal) |
| 3 | **Deal sourcing** | "Give me all sites in Raleigh over 3 acres... owned privately... give me their phone numbers" | High (growth lever) |
| 4 | **Cross-vertical business plan sync** | "If there's a gap in communication, it fails" | High (risk/failure prevention) |

---

## Recommended Build Order (from Follow-Up Email + Analysis)

### Why This Order Matters

The follow-up email made a key call: **build inward before outward.** Deal sourcing sounds exciting but depends on real-time broker context that can't be systematized yet. Contracts are fully internal, fully proprietary, fully buildable right now.

```
Phase 1 → Contract RAG System          (closed data, internal, highest ROI)
Phase 2 → Financial Model Generator    (semi-open data, every deal needs this)
Phase 3 → Business Plan Sync Layer     (cross-vertical intelligence feed)
Phase 4 → Deal Sourcing Bot            (external data, outreach automation)
```

---

## Prototype 1: Contract RAG System

### What It Does
A semantic search and retrieval system over Fallon's historical contracts (loan agreements, JV agreements, construction contracts, architect agreements). When entering a new negotiation, Danny or his lawyers can ask plain-English questions and get answers pulled from their own precedent documents instantly.

### Example Queries It Enables
- *"What delay penalty language did we use in our last three construction contracts?"*
- *"What indemnification structure did we use in JV agreements with pension fund LPs?"*
- *"What developer fee ranges have we accepted across recent deals?"*
- *"Compare our last two loan agreements on recourse provisions."*

### Why It's the Right Start
- Fully closed data environment (Danny raised privacy as a concern — this solves it)
- No new data collection required — the contracts already exist
- Directly addresses the highest-cost pain point Danny named
- The infrastructure built here (document ingestion → vector DB → retrieval → Claude) is **reusable for every other prototype**

### Workflow It Replaces
```
BEFORE:
Lawyer gets new deal → references memory + old PDFs → manually redlines →
sends to counterparty → back-and-forth for weeks → $$$

AFTER:
Lawyer gets new deal → queries RAG system in plain English →
gets Fallon's own precedent language surfaced instantly →
starts from strong position → fewer rounds → faster close
```

### Tech Stack
- **Document ingestion:** PyMuPDF or pdfplumber (PDF → text)
- **Chunking + embedding:** LangChain text splitter + OpenAI/Claude embeddings
- **Vector storage:** ChromaDB (local, simple) or pgvector via Supabase (if we want persistent)
- **Retrieval:** LangChain RAG chain or LlamaIndex
- **LLM:** Claude API (already in use at Fallon)
- **Interface:** Simple Streamlit or Gradio UI — search bar + results + source citations

### Prototype Scope (MVP)
- Upload 3–5 sample contracts (can use redacted/dummy versions to prototype)
- Query interface that returns: answer + source document + relevant excerpt
- No auth, no deployment — local proof of concept first

---

## Prototype 2: Financial Model Generator

### What It Does
Takes a set of project parameters as input (location, program type, acreage, timing, target IRR) and generates a structured pro forma shell — pre-populated with market-rate assumptions — that Fallon's team then refines with real broker/market data.

### Danny's Exact Words
*"Give me a financial model for a mixed use project that starts with a hotel, then a residential building, then an office building. I need a full pro forma."*

### What It Solves
Right now building a 100+ variable pro forma from scratch is slow. The goal is to get to 90% of a working model instantly — with clearly flagged assumptions — so the team spends time validating and adjusting rather than building from zero.

### Workflow It Changes
```
BEFORE:
New deal identified → analyst builds pro forma from scratch (days) →
reviewed → iterated → 100+ variables filled one by one

AFTER:
New deal identified → input key parameters into model generator →
structured pro forma output in minutes with flagged assumptions →
analyst fills in real broker data for the 10-20 variables that matter most
```

### Key Input Variables (What the Form Collects)
- Market / submarket
- Program: hotel / residential / office / mixed-use combination
- Acreage / GFA targets
- Target exit timeline
- Target LP IRR and equity multiple
- Construction cost benchmarks (regional)
- Projected lease-up timeline

### Output Format
- Excel-compatible structured output OR
- Clean formatted table in-app with export
- Every assumption labeled as "estimated" vs "confirmed" with source

### Tech Stack
- Claude API with a structured prompt + output schema
- Python backend (FastAPI or simple script)
- Streamlit UI for inputs/outputs
- Optional: pandas for table formatting, openpyxl for Excel export

### Prototype Scope (MVP)
- Single program type first (e.g., mixed-use: resi + office)
- Web form UI → structured pro forma output
- All assumptions clearly labeled, exportable

---

## Prototype 3: Business Plan Sync / Market Intelligence Feed

### What It Does
A lightweight system that monitors key market variables (interest rates, cap rates, construction costs, office absorption rates) and surfaces alerts when the underlying assumptions of an active business plan drift materially from current market conditions.

### The Problem It Solves (Danny's 2018 Example)
Projects underwritten in 2018 had to be restructured when:
- Interest rates shot up
- Investor return thresholds increased ~100 bps
- Office market deteriorated post-COVID

The development team kept executing on stale assumptions because the investments team was not getting real-time signals fast enough.

### What It Looks Like
```
Active Business Plan → stored assumptions (cap rate: 5.2%, construction cost: $380/sf, target IRR: 14%)
         ↓
Market Intelligence Monitor (runs daily/weekly)
         ↓
If: current market cap rate drifts >50 bps from underwriting assumption
Then: alert investments team → "Nashville multifamily cap rate now at 5.7% vs 5.2% underwrote.
      IRR impact: -180 bps. Business plan review recommended."
```

### Data Sources (Open Web)
- Federal Reserve / FRED for interest rate data
- CoStar / CBRE reports for cap rates (public summaries)
- ENR Construction Cost Index for build cost benchmarks
- BLS for employment/population data

### Tech Stack
- Python data fetching (requests + BeautifulSoup or APIs where available)
- Claude API for natural language summary of drift
- Simple dashboard: Streamlit showing active deals + current vs underwritten assumptions
- Email/Slack alert when threshold exceeded

### Prototype Scope (MVP)
- 2–3 key variables monitored (interest rates, one cap rate proxy)
- 1 sample "active deal" with stored underwriting assumptions
- Alert output when assumptions drift beyond threshold

---

## Prototype 4: Deal Sourcing Bot

### What It Does
Automates the early-stage site identification and initial outreach process. Takes Fallon's acquisition criteria (market, acreage, zoning type, proximity constraints) and searches for matching sites + property owner contacts, then drafts outreach messages.

### Danny's Exact Words
*"Give me all of the sites in the Raleigh Durham market that are over three acres within X miles of a highway, owned privately... and give me the phone numbers of all the owners. Some sort of deal sourcing bot."*

### Why This Is Phase 4 (Not Phase 1)
- Depends heavily on data quality and real-time broker context
- The human relationship layer (brokers, municipalities, MBTA programs) is hard to replace entirely
- More useful once internal data infrastructure is solid
- Highest complexity, most moving parts

### What It Still Does Usefully at MVP Level
- Parcel data lookup by criteria (public GIS data in most markets)
- Owner contact enrichment (county assessor records, public data APIs)
- Draft outreach message generation based on site specifics
- Track outreach status across prospects

### Tech Stack
- Public parcel/GIS APIs (most counties have these)
- Web scraping for county assessor data where no API exists
- Claude API for outreach message drafting
- Simple CRM-style interface to track leads

### Prototype Scope (MVP)
- Single market (Charlotte or Nashville — simpler permitting data)
- Criteria input form → list of matching parcels with owner info
- One-click outreach draft generation per parcel

---

## Cross-Cutting Technical Foundation

All four prototypes share the same core infrastructure. Build it once, reuse it everywhere.

```
Document Ingestion Layer
    → PDF/Excel → text → chunked → embedded → stored in vector DB

Retrieval Layer
    → Query → semantic search → top-k relevant chunks → passed to Claude

Claude API Layer
    → Context window: relevant retrieved chunks + system prompt + user query
    → Output: structured answer, pro forma, alert, or draft message

Interface Layer
    → Streamlit (fast, Python-native, no frontend overhead)
    → Separate page per prototype, unified nav
```

---

## What We Are NOT Building (And Why)

| Idea | Why We're Skipping It |
|------|-----------------------|
| Generic chatbot over Fallon's company docs | Too broad, low specificity, not addressing a named pain point |
| Full contract negotiation AI | This is lawyer territory — RAG for precedent surfacing is the right scope |
| Vertically integrated data platform | Too complex for prototype stage; build blocks first |
| Anything requiring Fallon's real data | Prototypes use sample/dummy data — we present the concept, they validate with real data |

---

## Files To Build (Folder Structure)

```
FallonPrototype/
├── IDEA_MAP.md                    ← this file
├── 01_contract_rag/
│   ├── README.md
│   ├── ingest.py                  (load + chunk + embed docs)
│   ├── query.py                   (RAG retrieval + Claude answer)
│   ├── app.py                     (Streamlit UI)
│   └── sample_contracts/          (dummy contract PDFs for demo)
├── 02_financial_model_generator/
│   ├── README.md
│   ├── model_generator.py         (prompt → structured pro forma)
│   └── app.py                     (Streamlit form UI)
├── 03_market_intelligence/
│   ├── README.md
│   ├── data_fetch.py              (pull key market variables)
│   ├── drift_monitor.py           (compare vs underwriting assumptions)
│   └── app.py                     (dashboard + alerts)
└── 04_deal_sourcing/
    ├── README.md
    ├── parcel_search.py            (GIS/assessor data lookup)
    ├── outreach_drafter.py         (Claude drafts outreach per parcel)
    └── app.py                      (Streamlit CRM-style interface)
```

---

## Questions to Answer Before Building Prototype 1

1. Do we have sample contracts to work from (even redacted/dummy versions)?
2. Is the Claude API key already set up in this project (main.py reference)?
3. Do we want local ChromaDB storage or Supabase (persistent, hosted)?
4. Is the Streamlit UI the right delivery format, or does Danny prefer something else?

---

## Summary: The Right First Build

Start with **Prototype 1 — Contract RAG**. It is:
- Fully self-contained (no external data dependencies)
- Directly addresses the highest-cost pain point Danny named
- Demonstrable in a single session
- The foundational layer everything else builds on

Once that works and can be shown to Danny, the rest of the roadmap follows naturally.
