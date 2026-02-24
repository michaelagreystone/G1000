# Fallon Unified RAG System — Phased Build Plan
> One system. Two sub-agents. Contract research + financial modeling from the same interface.
> Every phase is independently executable. Work top to bottom.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT UI                         │
│         Single chat-style input + tabbed output         │
└─────────────────────────┬───────────────────────────────┘
                          │ user query
                          ▼
┌─────────────────────────────────────────────────────────┐
│               ORCHESTRATOR AGENT                        │
│   Reads the query, classifies intent, routes to the     │
│   correct sub-agent, merges output back to the user     │
└────────────┬─────────────────────────┬──────────────────┘
             │ contract intent          │ financial model intent
             ▼                          ▼
┌────────────────────┐      ┌───────────────────────────┐
│  CONTRACT RAG      │      │  FINANCIAL MODEL          │
│  SUB-AGENT         │      │  SUB-AGENT                │
│                    │      │                           │
│  Retrieves clause  │      │  Retrieves historical     │
│  precedent from    │      │  deal comps + injects     │
│  contract vector   │      │  market defaults →        │
│  store → Claude    │      │  generates structured     │
│  answers with      │      │  pro forma with labeled   │
│  citations         │      │  assumptions              │
└────────┬───────────┘      └────────────┬──────────────┘
         │                               │
         └──────────────┬────────────────┘
                        ▼
          ┌─────────────────────────┐
          │   SHARED VECTOR STORE   │
          │                         │
          │  Collection A: Contracts │
          │  Collection B: Deal Data │
          │  Collection C: Market    │
          │              Defaults    │
          └─────────────────────────┘
```

**The key design principle:** Both sub-agents draw from the same vector store and use the same Claude client. The orchestrator is what makes this feel like one tool rather than two separate apps. The user never needs to know which sub-agent handled their query.

---

## Phase 0 — Project Foundation

**Issue:** Both sub-agents share infrastructure. Building that shared layer first means never duplicating setup work. Everything in Phase 0 is reused in every phase that follows.

---

### Phase 0.1 — Environment & Dependencies

**Issue:** The project needs a clean, reproducible environment. The existing `main.py` uses NVIDIA/Llama — the Fallon prototype uses Anthropic/Claude and its own dependency set. These need to be isolated so neither conflicts with the other.

**Tasks:**

- [ ] **0.1.1 — Create the FallonPrototype package structure**
  Inside `FallonPrototype/`, create the following empty folders and `__init__.py` files to make the project importable as a package:
  ```
  FallonPrototype/
  ├── shared/
  │   └── __init__.py
  ├── agents/
  │   └── __init__.py
  ├── data/
  │   ├── contracts/        ← sample contract PDFs live here
  │   ├── deal_data/        ← historical pro forma data lives here
  │   └── market_defaults/  ← JSON market assumption files live here
  ├── vector_store/         ← ChromaDB persists here (gitignored)
  └── __init__.py
  ```

- [ ] **0.1.2 — Create requirements.txt**
  Create `FallonPrototype/requirements.txt` with the following pinned dependencies:
  ```
  anthropic>=0.40.0
  chromadb>=0.5.0
  sentence-transformers>=3.0.0
  pdfplumber>=0.11.0
  langchain-text-splitters>=0.3.0
  streamlit>=1.40.0
  pandas>=2.2.0
  openpyxl>=3.1.0
  python-dotenv>=1.0.0
  tqdm>=4.66.0
  ```
  Note: `sentence-transformers` is used for embeddings locally (no API cost, runs on CPU fine for small document sets). This avoids a second API key dependency just for embeddings.

- [ ] **0.1.3 — Create .env and .env.example**
  Create `FallonPrototype/.env.example`:
  ```
  ANTHROPIC_API_KEY=your_key_here
  ```
  Create the actual `FallonPrototype/.env` with the real key. Add `.env` and `vector_store/` to `.gitignore` so neither the key nor the local database gets committed.

- [ ] **0.1.4 — Verify the Anthropic SDK connects**
  Create `FallonPrototype/shared/test_connection.py`. Write a minimal script that initializes the Anthropic client from the `.env` key, sends a one-line message (`"Reply with the word CONNECTED"`), and prints the response. Run it. If it prints `CONNECTED`, the foundation is solid. If it fails, fix the API key setup before touching anything else.

---

### Phase 0.2 — Shared Claude Client

**Issue:** Both sub-agents call Claude. If each one initializes its own client with its own settings, changes to things like model version, temperature, or retry logic have to be updated in two places. Centralizing it prevents drift.

**Tasks:**

- [ ] **0.2.1 — Build the shared Claude client module**
  Create `FallonPrototype/shared/claude_client.py`. Initialize a single `anthropic.Anthropic()` client using the key from `.env`. Set a module-level constant `MODEL = "claude-sonnet-4-6"`. Export both the client and the model constant so every agent imports from this one file.

- [ ] **0.2.2 — Write a standard `call_claude()` utility function**
  In the same file, write:
  ```python
  def call_claude(system_prompt: str, user_message: str, max_tokens: int = 2048) -> str
  ```
  This function: calls `client.messages.create()` with the shared model, passes the system and user content, handles `anthropic.APIStatusError` with a clean error message (not a stack trace), and returns the response text as a plain string. All four agents — orchestrator, contract sub-agent, financial sub-agent, and any future agents — call this single function. Never call the API directly from agent files.

- [ ] **0.2.3 — Add a token usage tracker**
  Wrap `call_claude()` so it logs the `input_tokens` and `output_tokens` from every API response to a session-level counter stored in a module-level dict. Add a `get_session_usage() -> dict` function that returns total tokens used and estimated cost (at Claude Sonnet pricing: ~$3/M input, ~$15/M output). This shows up in the Streamlit sidebar so cost is always visible during demos.

---

### Phase 0.3 — Shared Vector Store

**Issue:** The Contract sub-agent searches contracts. The Financial Model sub-agent searches historical deal data and market defaults. Both use the same ChromaDB instance — just different collections within it. Setting up the store once and sharing it prevents running two separate databases.

**Tasks:**

- [ ] **0.3.1 — Initialize the ChromaDB client**
  Create `FallonPrototype/shared/vector_store.py`. Initialize a persistent ChromaDB client pointed at `FallonPrototype/vector_store/`. This path is where the database files live on disk — they persist between app restarts.

- [ ] **0.3.2 — Define the three collections**
  In the same file, create (or get if already existing) three named collections:
  - `fallon_contracts` — chunks from contract PDFs
  - `fallon_deal_data` — chunks from historical pro formas and deal memos
  - `fallon_market_defaults` — structured market assumption records

  Each collection uses the same embedding function (SentenceTransformer `all-MiniLM-L6-v2` — fast, local, no API cost). Wrap collection creation in a `get_collection(name: str)` function that returns the collection object, creating it if it doesn't exist yet.

- [ ] **0.3.3 — Build the shared `add_documents()` function**
  Write `add_documents(collection_name: str, texts: list[str], metadatas: list[dict], ids: list[str])` that: checks whether each document ID already exists in the collection before adding (deduplication), embeds the texts using the SentenceTransformer model, and upserts them into the collection. Print a summary: `"Added X new documents to [collection_name]. Y already existed, skipped."`

- [ ] **0.3.4 — Build the shared `query_collection()` function**
  Write `query_collection(collection_name: str, query_text: str, n_results: int = 5) -> list[dict]` that: embeds the query text, queries the specified collection for the top-n most similar documents, and returns a list of dicts: `{text, metadata, distance}`. Distance is the raw ChromaDB similarity score — lower is more similar (cosine distance). Include it in all results so the calling agent can apply confidence filters.

---

## Phase 1 — Document Ingestion Pipeline

**Issue:** The vector store is only as good as what's been ingested into it. Both sub-agents need clean, well-chunked text from their respective data sources before any query can be answered. This phase builds the ingestion pipeline that feeds all three collections.

---

### Phase 1.1 — Contract Ingestion

**Issue:** Contracts are PDFs with dense legal formatting. Bad parsing — including page numbers, running headers, footnotes, and table of contents pages — pollutes the chunks and degrades retrieval. The ingestion must produce clean, clause-level text.

**Tasks:**

- [ ] **1.1.1 — Create sample contract files**
  Populate `FallonPrototype/data/contracts/` with 4–5 dummy contract PDFs representing the types Danny named. Use publicly available legal templates or AI-generated contracts with realistic clause structure. Required types:
  - `loan_agreement_sample.pdf` — construction loan, including recourse provisions, draw schedule, events of default
  - `jv_agreement_sample.pdf` — joint venture with LP/GP waterfall, promote structure, capital call provisions
  - `construction_contract_sample.pdf` — GMP contract, delay penalties, substantial completion definition, change order process
  - `architect_agreement_sample.pdf` — AIA-style, scope of services, fee structure, termination for convenience
  - `lease_agreement_sample.pdf` — office NNN lease, free rent provisions, TI allowance, holdover terms
  These files are the demo corpus. Label them clearly as samples in the filename.

- [ ] **1.1.2 — Build the contract PDF parser**
  Create `FallonPrototype/shared/ingest_contracts.py`. Write `parse_contract_pdf(filepath: str) -> str` using `pdfplumber`. For each page: extract the text, strip page numbers (regex: remove lines that are purely numeric or `"Page X of Y"`), strip running headers/footers (detect lines that repeat across 3+ pages and remove them), and join the remaining text. Return the full cleaned text of the document as a single string.

- [ ] **1.1.3 — Build the contract chunker**
  In the same file, write `chunk_contract(text: str, doc_name: str) -> list[dict]` that uses LangChain's `RecursiveCharacterTextSplitter` with:
  - `chunk_size=900` (characters, not tokens — contracts have short sentences)
  - `chunk_overlap=150` (ensures clause cross-references aren't split)
  - `separators=["\n\n", "\n", ". ", " "]` (prioritize splitting at paragraph breaks)

  For each chunk, return a dict: `{text, metadata: {source: doc_name, doc_type, chunk_index, total_chunks}}`. The metadata is what allows the sub-agent to cite exactly which document a clause came from.

- [ ] **1.1.4 — Build the contract ingestion runner**
  Write `run_contract_ingestion()` that: iterates over every PDF in `data/contracts/`, parses and chunks each one, calls `add_documents()` on the `fallon_contracts` collection, and prints a final count. Make this runnable as a standalone script: `python -m FallonPrototype.shared.ingest_contracts`. It should be safe to re-run — deduplication in Phase 0.3.3 prevents double-indexing.

- [ ] **1.1.5 — Manually validate 10 chunks**
  After running ingestion, write a quick test in `test_ingestion.py` that prints 10 random chunks from `fallon_contracts`. Read each one and check: (a) Is it a self-contained legal thought? (b) Does it contain any page number artifacts or header pollution? (c) Is the metadata correct? Adjust chunk size or cleaning regex until all 10 pass a visual read-through.

---

### Phase 1.2 — Deal Data Ingestion

**Issue:** The Financial Model sub-agent needs historical deal context to generate relevant pro formas. This means past deal memos, previous pro formas, and any structured data about completed or active projects. This data doesn't exist as real files yet — we build representative sample data.

**Tasks:**

- [ ] **1.2.1 — Create sample deal data files**
  Populate `FallonPrototype/data/deal_data/` with structured sample files representing Fallon's deal history. Create at minimum:
  - `nashville_mixed_use_deal_memo.txt` — narrative deal memo describing site, program, business plan rationale, target returns
  - `charlotte_multifamily_proforma.txt` — text representation of a pro forma (not a live spreadsheet — convert key assumptions and outputs to readable text so it can be chunked and embedded)
  - `boston_office_deal_summary.txt` — completed deal summary with actual vs projected returns, lessons learned
  Each file should contain realistic numbers and structure. These are the "institutional memory" the Financial Model sub-agent draws from when generating new models.

- [ ] **1.2.2 — Build the deal data ingestion script**
  Create `FallonPrototype/shared/ingest_deal_data.py`. Since deal data files are `.txt` rather than PDF, parsing is simpler — read with `open()` and split by paragraph. Use the same `RecursiveCharacterTextSplitter` as contracts but with slightly larger chunks (`chunk_size=1200`) because deal memo prose is denser and more context-dependent than legal clauses. Metadata per chunk: `{source: filename, deal_type, market, program_type, year}`.

- [ ] **1.2.3 — Run ingestion into `fallon_deal_data` collection**
  Call `add_documents()` targeting the `fallon_deal_data` collection. Validate with a test query: `"What were the return assumptions for the Nashville project?"` — the top result should be from the Nashville deal memo. If not, review chunking or metadata tagging.

---

### Phase 1.3 — Market Defaults Ingestion

**Issue:** The Financial Model sub-agent needs baseline market assumptions to pre-populate a pro forma. These aren't documents to search — they're structured records to retrieve by market and program type. They need to be stored differently from contracts and deal memos.

**Tasks:**

- [ ] **1.3.1 — Build the market defaults JSON**
  Create `FallonPrototype/data/market_defaults/market_defaults.json`. Structure it as a nested dict: `market → program_type → variable → value`. Include at minimum:

  ```json
  {
    "charlotte": {
      "multifamily": {
        "rent_psf_monthly": 1.95,
        "construction_cost_psf": 275,
        "exit_cap_rate_pct": 5.25,
        "stabilized_occupancy_pct": 94,
        "lease_up_months": 18,
        "soft_cost_pct_of_hard": 22,
        "developer_fee_pct": 4,
        "construction_loan_ltc_pct": 65,
        "construction_loan_rate_pct": 7.75,
        "target_lp_irr_pct": 15,
        "target_equity_multiple": 1.85
      },
      "office": { ... },
      "hotel": { ... }
    },
    "nashville": { ... },
    "boston": { ... }
  }
  ```

  Every value should have a companion `_source` key: `"rent_psf_monthly_source": "Charlotte broker market data, Q4 2025"`. This source label flows all the way through to the generated pro forma so the user always knows what to verify.

- [ ] **1.3.2 — Ingest market defaults as vector documents**
  Convert each market/program combination into a human-readable text block and embed it into the `fallon_market_defaults` collection. Example text for one record:
  `"Charlotte multifamily market defaults (Q4 2025): Monthly rent $1.95/sf, construction cost $275/sf, exit cap rate 5.25%, stabilized occupancy 94%, lease-up 18 months, soft costs 22% of hard, developer fee 4%, construction loan LTC 65% at 7.75%, target LP IRR 15%, target equity multiple 1.85x."`
  Metadata: `{market: "charlotte", program_type: "multifamily", last_updated: "2025-12-01"}`. The text format allows semantic retrieval — the sub-agent can ask "what are Charlotte multifamily assumptions?" and get these back as context.

- [ ] **1.3.3 — Add a direct lookup function**
  In addition to vector retrieval, write `get_market_defaults(market: str, program_type: str) -> dict` in `vector_store.py` that loads `market_defaults.json` directly and returns the structured dict for the requested market/program. The Financial Model sub-agent uses this for precise value injection — vector retrieval is for context, direct lookup is for numbers that need to be exact.

---

## Phase 2 — Orchestrator Agent

**Issue:** The user types one query. The system needs to figure out whether it's a contract question or a financial modeling request and route it correctly — without the user having to pick a mode or navigate between tabs. The orchestrator is what makes this feel like one intelligent system rather than two separate tools bolted together.

---

### Phase 2.1 — Intent Classification

**Issue:** Routing errors are the most damaging failure mode in a multi-agent system. If a contract question gets sent to the financial model sub-agent or vice versa, the answer will be wrong and trust is lost. The classifier needs to be fast, reliable, and handle ambiguous queries gracefully.

**Tasks:**

- [ ] **2.1.1 — Define the intent taxonomy**
  Document in `agents/orchestrator.py` the two primary intents and their distinguishing characteristics as inline comments:

  `CONTRACT_RESEARCH`: User is asking about contract language, clause precedent, legal terms, negotiation history, or document-specific questions. Trigger phrases: "what did we use", "what language", "what have we accepted", "what do our contracts say", "indemnification", "recourse", "termination", "developer fee terms", "delay penalty", "JV structure."

  `FINANCIAL_MODEL`: User is asking to generate, build, or model a pro forma, project return analysis, or financial scenario. Trigger phrases: "build a model", "generate a pro forma", "what would returns look like", "model a deal", "underwrite", "IRR", "equity multiple", "construction cost estimate", "what would it cost to develop."

  `AMBIGUOUS`: The query contains elements of both or neither. Handle separately.

- [ ] **2.1.2 — Write the intent classification function**
  Create `FallonPrototype/agents/orchestrator.py`. Write `classify_intent(query: str) -> str` that calls `call_claude()` with a tightly scoped system prompt. The prompt instructs Claude to read the query and return ONLY one of three words: `CONTRACT_RESEARCH`, `FINANCIAL_MODEL`, or `AMBIGUOUS`. No explanation, no punctuation — just the classification word. Parse the response with `.strip()` and validate it's one of the three expected values. If not, default to `AMBIGUOUS`. This strict output format prevents the classifier from drifting into conversational responses.

- [ ] **2.1.3 — Build an AMBIGUOUS query handler**
  Write `handle_ambiguous(query: str) -> str` that returns a clarification prompt to the user. Example: `"I can help with contract research (searching your historical contract language for precedent) or financial modeling (generating a pro forma for a new deal). Which would be more useful for your question?"` Display this as a follow-up in the Streamlit UI — a two-button choice: [Search Contracts] [Build Financial Model]. On click, re-run the query with the explicit intent.

- [ ] **2.1.4 — Test the classifier with 20 sample queries**
  Write `test_orchestrator.py` with a list of 20 test queries — 8 clearly contract, 8 clearly financial, 4 ambiguous. Run each through `classify_intent()` and assert the expected output. All 20 should pass before moving on. If any contract queries are misclassified as financial or vice versa, refine the classification prompt. Classification accuracy must be 100% on this test set before building the sub-agents.

---

### Phase 2.2 — Routing & Response Merging

**Issue:** After classification, the orchestrator needs to dispatch the query to the right sub-agent, receive the structured response, and format it consistently for the UI. The UI should receive the same response shape regardless of which sub-agent ran.

**Tasks:**

- [ ] **2.2.1 — Define the standard response schema**
  In `agents/orchestrator.py`, define a `AgentResponse` dataclass:
  ```python
  @dataclass
  class AgentResponse:
      intent: str              # "CONTRACT_RESEARCH" or "FINANCIAL_MODEL"
      answer: str              # Main text response from Claude
      sources: list[str]       # Source document names (contracts) or assumption sources (models)
      raw_chunks: list[dict]   # Retrieved vector chunks (for contracts) or model data (for financial)
      confidence: str          # "high" / "medium" / "low" — based on retrieval scores
      export_data: dict | None # Structured data for Excel export (financial model only, else None)
  ```
  Both sub-agents return this exact structure. The UI only needs to know how to render one response type.

- [ ] **2.2.2 — Build the main `route_query()` function**
  Write `route_query(query: str) -> AgentResponse` that: (1) calls `classify_intent()`, (2) if `CONTRACT_RESEARCH`, calls `contract_agent.run(query)`, (3) if `FINANCIAL_MODEL`, calls `financial_agent.run(query)`, (4) if `AMBIGUOUS`, returns an `AgentResponse` with `answer` set to the clarification prompt and `intent="AMBIGUOUS"`. This is the single function the Streamlit UI calls — it never directly invokes a sub-agent.

- [ ] **2.2.3 — Add query logging**
  Before routing, log every query to a session log: `{timestamp, query, classified_intent, tokens_used}`. Write this to `FallonPrototype/query_log.jsonl` — one JSON object per line. This file becomes valuable for reviewing what users are asking most frequently and refining the system over time.

---

## Phase 3 — Contract RAG Sub-Agent

**Issue:** This sub-agent receives a contract-related query, retrieves the most relevant clauses from the `fallon_contracts` vector collection, and asks Claude to synthesize an answer that is grounded entirely in those retrieved clauses — never in general legal knowledge. The output must include exact source citations so a lawyer can verify every claim.

---

### Phase 3.1 — Retrieval Strategy

**Issue:** Not all contract queries are the same. "What delay penalty language did we use?" requires retrieving specific clauses. "How have our JV waterfall structures compared across deals?" requires retrieving and comparing across multiple documents. A single retrieval call handles the first — the second needs multi-document retrieval with grouping logic.

**Tasks:**

- [ ] **3.1.1 — Build the primary retrieval function**
  Create `FallonPrototype/agents/contract_agent.py`. Write `retrieve_contract_clauses(query: str, n_results: int = 6) -> list[dict]` that calls `query_collection("fallon_contracts", query, n_results)`. Return the results as-is plus a computed `relevance_label`: if distance < 0.3 → `"high"`, 0.3–0.5 → `"medium"`, > 0.5 → `"low"`. Never pass low-relevance chunks to Claude — they add noise.

- [ ] **3.1.2 — Add a cross-document comparison mode**
  Detect when a query contains comparison language: "compare", "across deals", "different contracts", "how have we", "what range." When detected, set `n_results=10` and add a grouping step: sort retrieved chunks by `metadata.source` (document name) and group them so Claude receives one chunk per document where possible. This ensures comparative answers draw from multiple contracts rather than returning 6 chunks from the same document.

- [ ] **3.1.3 — Add a document-type filter**
  Some queries are contract-type-specific: "What do our loan agreements say about..." should only search `fallon_contracts` chunks where `metadata.doc_type == "loan_agreement"`. Parse the query for doc-type signals (loan, JV, joint venture, construction contract, architect) and pre-filter the ChromaDB query using the `where` parameter: `{"doc_type": {"$eq": "loan_agreement"}}`. This dramatically improves precision for type-specific queries.

---

### Phase 3.2 — Answer Generation

**Issue:** The quality of the Claude answer depends entirely on the system prompt. Legal research has zero tolerance for hallucination — the prompt must structurally prevent it while still generating answers that are useful, not just quote-dumps.

**Tasks:**

- [ ] **3.2.1 — Write the Contract sub-agent system prompt**
  In `contract_agent.py`, define the system prompt as a module-level constant. It must instruct Claude to:
  1. Act as a legal research assistant for a real estate development firm with a $6B pipeline
  2. Answer questions using ONLY the provided contract excerpts — never from general legal knowledge
  3. For every claim, cite the source document in brackets: `[Loan Agreement Sample, Clause 7.2]`
  4. If the same clause appears across multiple contracts, note the pattern: `"Across three reviewed agreements, delay penalties ranged from..."`
  5. If no relevant clause is found, say explicitly: `"The provided contracts do not contain precedent on this topic"` — never fabricate
  6. Close every answer with a `"Gaps & Recommendations"` section: note if the retrieved precedent is limited and recommend what a lawyer should verify or negotiate fresh

- [ ] **3.2.2 — Build the context formatter**
  Write `format_contract_context(chunks: list[dict]) -> str` that takes the retrieved chunks and formats them into a readable context block for the Claude prompt. Format each chunk as:
  ```
  --- SOURCE: [filename] | TYPE: [doc_type] | RELEVANCE: [high/medium/low] ---
  [chunk text]
  ```
  Separate chunks with a blank line. This formatting makes it visually clear to Claude where one document ends and another begins — critical for accurate citation.

- [ ] **3.2.3 — Build `contract_agent.run()`**
  Write the main `run(query: str) -> AgentResponse` function that: (1) retrieves chunks, (2) filters out low-relevance chunks, (3) formats the context, (4) calls `call_claude(system_prompt, context + query)`, (5) determines overall confidence (high if all chunks are high-relevance, medium if mixed, low if majority are medium), and (6) returns a fully populated `AgentResponse`. Source list = unique document filenames from the retrieved chunks.

- [ ] **3.2.4 — Test with the 5 core Fallon contract queries**
  Run the complete contract agent against these queries and manually evaluate each response:
  1. `"What delay penalty language have we used in construction contracts?"`
  2. `"What indemnification terms appear in our JV agreements?"`
  3. `"What developer fee structures have we accepted?"`
  4. `"Compare recourse provisions across our loan agreements."`
  5. `"What termination for convenience clauses appear in architect agreements?"`

  Evaluate each on: (a) Is the answer grounded only in retrieved text? (b) Are citations accurate? (c) Is anything hallucinated? (d) Is the Gaps & Recommendations section useful? Fix the prompt before proceeding.

---

## Phase 4 — Financial Model Sub-Agent

**Issue:** This sub-agent receives a financial modeling request, retrieves relevant historical deal data and market defaults, and generates a structured pro forma with every assumption clearly labeled as confirmed, estimated, or requiring broker verification. The output must be both readable in the UI and exportable to Excel.

---

### Phase 4.1 — Input Parsing

**Issue:** Financial modeling queries are unstructured: "Build me a model for a 200-unit apartment project in Charlotte" contains all the key parameters, but they need to be extracted cleanly before the model can be generated. Extracting them via Claude is more robust than regex parsing.

**Tasks:**

- [ ] **4.1.1 — Define the project parameters schema**
  In `FallonPrototype/agents/financial_agent.py`, define a `ProjectParameters` dataclass:
  ```python
  @dataclass
  class ProjectParameters:
      market: str               # "charlotte" | "nashville" | "boston" | "other"
      program_type: str         # "multifamily" | "office" | "hotel" | "mixed_use"
      unit_count: int | None    # for residential
      total_gfa_sf: int | None  # gross floor area in sq ft
      target_lp_irr: float | None
      target_equity_multiple: float | None
      construction_start: str | None  # free text — "Q3 2026", "next year", etc.
      notes: str                # any additional context from the query
  ```

- [ ] **4.1.2 — Build the parameter extraction function**
  Write `extract_parameters(query: str) -> ProjectParameters` that calls `call_claude()` with a prompt that instructs Claude to read the query and return a JSON object matching the `ProjectParameters` schema. Include explicit instructions to use `null` for any field not mentioned in the query rather than guessing. Parse the JSON response with `json.loads()` and hydrate the dataclass. Wrap in a try/except — if JSON parsing fails, return a `ProjectParameters` with all fields null and let the sub-agent handle the gaps.

- [ ] **4.1.3 — Build a missing-parameters prompt**
  Write `check_missing_parameters(params: ProjectParameters) -> list[str]` that returns a list of field names that are null but required for model generation. Required fields are: `market` and `program_type`. Everything else is optional (defaults will be used). If market or program_type is null, return a clarification message to the user before attempting generation: `"To build your model I need: market (Charlotte / Nashville / Boston) and program type (multifamily / office / hotel). Which are you modeling?"` — displayed as a follow-up in the UI.

---

### Phase 4.2 — Context Retrieval for the Model

**Issue:** The financial sub-agent needs two types of context: (1) historical deal data — what have Fallon's past comparable deals looked like? — and (2) current market defaults — what are the baseline assumptions for this market/program today? Combining both gives the generated model historical grounding plus current market relevance.

**Tasks:**

- [ ] **4.2.1 — Build the deal comps retrieval function**
  Write `retrieve_deal_comps(params: ProjectParameters) -> list[dict]` that constructs a query string from the parameters (e.g., `"Charlotte multifamily residential development pro forma returns"`) and calls `query_collection("fallon_deal_data", query, n_results=3)`. Return the top 3 most relevant historical deal chunks. These are the "precedent" for the financial model — what Fallon has actually underwritten in comparable situations.

- [ ] **4.2.2 — Build the market defaults retrieval function**
  Write `retrieve_market_defaults(params: ProjectParameters) -> dict` that calls `get_market_defaults(params.market, params.program_type)` from the direct lookup function in Phase 1.3.3. If the exact market/program combination doesn't exist, fall back to the closest available (e.g., if "other" market, use national averages) and flag all values as `"estimated — no market-specific data available, verify with broker"`.

- [ ] **4.2.3 — Build the combined context formatter**
  Write `format_financial_context(deal_comps: list[dict], defaults: dict) -> str` that produces a structured context block for Claude. Section 1: "Historical Deal Comparables" — formatted deal comp chunks with source labels. Section 2: "Current Market Defaults" — the defaults dict formatted as a readable table with source labels on every value. This combined context is what Claude uses to populate the pro forma with informed assumptions rather than generic estimates.

---

### Phase 4.3 — Pro Forma Generation

**Issue:** Generating a structured financial model that is accurate enough to be useful but clearly labeled enough to not be trusted blindly is a prompt engineering problem as much as a technical one. The output needs to be parseable for Excel export and readable in the browser simultaneously.

**Tasks:**

- [ ] **4.3.1 — Define the pro forma output schema**
  In `financial_agent.py`, define the exact structure of the generated pro forma as a Python dict. Organize into five sections:
  ```
  {
    "project_summary": {deal_name, market, program_type, total_gfa, unit_count},
    "revenue_assumptions": {rent_psf, occupancy, lease_up_months, ...},
    "cost_assumptions": {construction_cost_psf, soft_cost_pct, developer_fee_pct, contingency_pct, ...},
    "financing_assumptions": {ltc_ratio, loan_rate, loan_term, equity_split, ...},
    "return_metrics": {projected_irr, equity_multiple, profit_on_cost, development_spread, ...}
  }
  ```
  Every leaf value is itself a dict: `{"value": 1.95, "unit": "$/sf/month", "label": "estimated", "source": "Charlotte multifamily market defaults, Q4 2025"}`. The `label` field is one of: `"confirmed"` (user-provided), `"estimated"` (from market defaults), or `"calculated"` (derived from other values).

- [ ] **4.3.2 — Write the Financial Model sub-agent system prompt**
  Define the system prompt as a module-level constant. It must instruct Claude to:
  1. Act as a real estate financial analyst for a merchant developer (build-stabilize-sell model)
  2. Generate a pro forma using ONLY the values from the provided market defaults and historical deal comps — never invent numbers from general knowledge
  3. Output the result as a valid JSON object matching the pro forma schema exactly
  4. Label every value's `label` field accurately: user-provided values → `"confirmed"`, values from market defaults → `"estimated"`, values derived mathematically → `"calculated"`
  5. If a required value is missing from both defaults and deal comps, set `value` to `null` and `label` to `"missing — broker input required"`
  6. Include a `"return_metrics"` section with the computed IRR, equity multiple, and profit-on-cost using the provided assumptions

- [ ] **4.3.3 — Build `financial_agent.run()`**
  Write `run(query: str) -> AgentResponse` that: (1) extracts parameters, (2) checks for missing required params, (3) retrieves deal comps and market defaults, (4) formats combined context, (5) calls `call_claude()` with the financial system prompt, (6) parses the JSON response into the pro forma schema dict, (7) runs validation checks (IRR in 5–35%, equity multiple in 1.2x–3.5x), and (8) returns `AgentResponse` with `answer` = a plain-English summary of the model ("Your Charlotte multifamily deal projects a 16.2% LP IRR and 1.9x equity multiple on a 200-unit project..."), `export_data` = the full pro forma dict, and `sources` = the market defaults sources and deal comp filenames.

- [ ] **4.3.4 — Build the return metrics calculator**
  Write a pure Python function `compute_return_metrics(pro_forma: dict) -> dict` that takes the generated pro forma and computes IRR, equity multiple, and profit-on-cost from the assumption values. This is a simplified DCF — not a full model — but it gives a sanity-check number that can be compared against Claude's generated metrics. If they differ by more than 15%, flag the discrepancy in the response.

- [ ] **4.3.5 — Test with three project types**
  Run `financial_agent.run()` with these queries and evaluate each output:
  1. `"Build me a model for a 200-unit multifamily project in Charlotte"`
  2. `"What would returns look like on a mixed-use office and hotel project in Nashville, targeting 15% LP IRR?"`
  3. `"Generate a pro forma for a 50-unit condo conversion in Boston"`
  Evaluate: Are all assumptions labeled correctly? Does the IRR pass the sanity check? Are any values null that should have been populated? Fix the prompt or defaults before building the UI.

---

### Phase 4.4 — Excel Export

**Issue:** The pro forma needs to leave the browser and land in an analyst's hands as a working Excel file. The structure needs to match how Fallon's team actually uses spreadsheets — tabbed by section, color-coded by assumption type, with an audit trail of sources.

**Tasks:**

- [ ] **4.4.1 — Build the Excel exporter**
  Create `FallonPrototype/shared/excel_export.py`. Write `export_pro_forma(pro_forma: dict, deal_name: str) -> bytes` using `openpyxl` that: creates a workbook with five sheets matching the pro forma sections (Project Summary, Revenue, Costs, Financing, Returns), populates each sheet with two columns (Variable Name, Value + Unit), color-codes rows by label (yellow = `"confirmed"`, light blue = `"estimated"`, white = `"calculated"`, red = `"missing"`), and returns the workbook as a bytes object (for Streamlit's `download_button`).

- [ ] **4.4.2 — Add an Assumptions & Sources sheet**
  Add a sixth sheet called "Assumptions & Sources" that lists every `"estimated"` value, its source string, and a note: `"Replace with confirmed broker data before final underwriting."` This is the audit trail that makes the model trustworthy and defensible to an LP.

- [ ] **4.4.3 — Add a sensitivity table to the Returns sheet**
  On the Returns sheet, below the base case metrics, add a 3x3 sensitivity table: rows = exit cap rate (base -50bps, base, base +50bps), columns = construction cost (base -10%, base, base +10%), cells = projected IRR for each combination. Compute these nine values using `compute_return_metrics()` with adjusted inputs. This is the first question any LP will ask — "what if cap rates move?" — and having it pre-built in the export makes the model immediately more useful.

---

## Phase 5 — Unified Streamlit UI

**Issue:** The UI is a single interface that routes to both sub-agents without the user needing to know the difference. The design goal is: looks like one smart assistant, not two tools with a toggle switch.

---

### Phase 5.1 — App Shell & Layout

**Tasks:**

- [ ] **5.1.1 — Build the main app shell**
  Create `FallonPrototype/app.py`. Set up a Streamlit app with:
  - Page title: "Fallon Intelligence System"
  - Wide layout (`st.set_page_config(layout="wide")`)
  - Sidebar containing: Fallon logo placeholder, token usage counter (from Phase 0.2.3), documents indexed count (contracts + deal data + market defaults), and a "Re-index Documents" button that re-runs all ingestion scripts

- [ ] **5.1.2 — Build the chat input area**
  In the main panel, create a single `st.text_area()` labeled `"Ask anything about your contracts or model a new deal"` with a placeholder: `"e.g., 'What delay penalty language have we used?' or 'Build a model for a 150-unit multifamily in Nashville'"`. Add a "Submit" button. This is the only input the user ever needs.

- [ ] **5.1.3 — Build the intent indicator**
  After query submission, show a small colored badge before the response loads indicating which sub-agent was called: a gray "Contract Research" tag or a blue "Financial Model" tag. This subtle signal educates users on what the system can do without making them pick a mode themselves.

---

### Phase 5.2 — Contract Research Response Display

**Tasks:**

- [ ] **5.2.1 — Display the contract answer**
  When `intent == "CONTRACT_RESEARCH"`, render the `answer` field in a styled markdown block. The answer already contains inline citations from the sub-agent — Streamlit's markdown renderer will display them correctly. Show a confidence badge (green/yellow/red) based on `AgentResponse.confidence`.

- [ ] **5.2.2 — Build the source excerpts expander**
  Below the answer, add an `st.expander("View Source Excerpts")` that, when opened, shows each retrieved chunk as a card: source document name in bold, relevance score as a percentage, and the chunk text in a light gray `st.code()` block. This lets lawyers verify the AI's claims against the actual contract language — essential for professional trust.

- [ ] **5.2.3 — Add a "Documents Not Found" state**
  If `confidence == "low"` and no high-relevance chunks were found, display a yellow warning box: "Limited contract precedent found for this query. The answer may be incomplete. Consider adding more contracts to the index or consulting your legal team directly." Never display a low-confidence answer without this flag.

---

### Phase 5.3 — Financial Model Response Display

**Tasks:**

- [ ] **5.3.1 — Display the return metrics summary**
  When `intent == "FINANCIAL_MODEL"`, show the return metrics at the top in large, bold callout boxes: IRR (%), Equity Multiple (x), and Profit-on-Cost (%). These are the headline numbers — a developer should see them immediately without scrolling.

- [ ] **5.3.2 — Display the full pro forma tables**
  Below the headline metrics, render the five pro forma sections as individual `st.dataframe()` tables. Each table has columns: Variable, Value, Unit, and Status. The Status column uses color coding: yellow for estimated, blue for confirmed, red for missing. Filter out `calculated` fields from the display unless the user toggles "Show All Fields."

- [ ] **5.3.3 — Add the assumption sources expander**
  Below the tables, add an `st.expander("View Assumption Sources")` listing every estimated value with its source string. Same pattern as the contract source expander — transparency builds trust.

- [ ] **5.3.4 — Add the Excel download button**
  Below the sources expander, add a `st.download_button("Download Model (.xlsx)", data=export_bytes, file_name=f"fallon_{deal_name}_model.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")`. The export runs on demand, not automatically — triggering it once the user is satisfied with the model in the UI.

- [ ] **5.3.5 — Add the adjust assumptions panel**
  After first generation, reveal a collapsible panel: "Adjust Assumptions." Show the key estimated values as editable `st.number_input()` fields. Add a "Recalculate" button that re-runs `compute_return_metrics()` with the adjusted values and updates the headline IRR/multiple/profit figures instantly — no new API call needed for simple adjustments.

---

### Phase 5.4 — Session History

**Tasks:**

- [ ] **5.4.1 — Build session history with `st.session_state`**
  Store every query-response pair in `st.session_state.history` as a list of `AgentResponse` objects. Display the last 5 as a scrollable history panel below the main response area, collapsed by default. Each entry shows: query text, intent badge, and a one-line summary of the response.

- [ ] **5.4.2 — Add a "Clear Session" button**
  In the sidebar, add a button that clears `st.session_state.history` and resets the token counter. Useful for starting a clean demo.

---

## Phase 6 — Integration Testing & Demo Prep

**Issue:** Each component has been tested in isolation. Before demo-ready status, the full end-to-end flow needs to be tested as a user would actually experience it — including edge cases and failure modes.

**Tasks:**

- [ ] **6.1 — Full end-to-end test: contract flow**
  Open the app fresh. Type: `"What developer fee structures have we accepted in our JV agreements?"` Verify: correct intent classification, relevant chunks retrieved, answer cites sources, source expander shows matching text, confidence badge is accurate.

- [ ] **6.2 — Full end-to-end test: financial model flow**
  Type: `"Build a model for a 150-unit multifamily project in Nashville targeting a 15% IRR."` Verify: parameters extracted correctly, market defaults populated, return metrics displayed, all estimated values labeled, Excel download produces a correctly formatted file.

- [ ] **6.3 — Test the ambiguous query flow**
  Type: `"What's the IRR on our JV agreements?"` — this is intentionally ambiguous (JV agreements are contracts, but IRR is a financial metric). Verify: classified as AMBIGUOUS, clarification prompt shown, clicking either option runs the correct sub-agent.

- [ ] **6.4 — Test the missing data state**
  Query something the contract index doesn't have: `"What do our contracts say about cryptocurrency payment clauses?"` Verify: low-confidence warning displays, answer acknowledges the gap rather than fabricating, source expander shows the weak retrievals.

- [ ] **6.5 — Test re-indexing**
  Add a new contract PDF to `data/contracts/` while the app is running. Click "Re-index Documents" in the sidebar. Verify: the new document is ingested, the document count updates, and a query about content from the new document returns relevant results.

- [ ] **6.6 — Write the demo script**
  Create `FallonPrototype/DEMO_SCRIPT.md` — a 10-minute walkthrough script for showing Danny the system. Sequence: (1) start with a contract query to show the legal precedent use case, (2) run a financial model query to show the pro forma generation, (3) demonstrate the Excel download, (4) show the adjust assumptions panel, (5) add a new contract via upload and immediately query it. End with a one-slide summary of what gets built next (Market Intelligence Feed).

---

## File Structure (Final)

```
FallonPrototype/
├── IDEA_MAP.md
├── PHASES.md
├── UNIFIED_RAG_PHASES.md         ← this file
├── DEMO_SCRIPT.md                ← Phase 6.6
├── requirements.txt
├── .env.example
├── .gitignore
├── app.py                        ← unified Streamlit launcher
│
├── shared/
│   ├── __init__.py
│   ├── claude_client.py          ← Phase 0.2
│   ├── vector_store.py           ← Phase 0.3
│   ├── ingest_contracts.py       ← Phase 1.1
│   ├── ingest_deal_data.py       ← Phase 1.2
│   ├── excel_export.py           ← Phase 4.4
│   └── test_connection.py        ← Phase 0.1.4
│
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py           ← Phase 2
│   ├── contract_agent.py         ← Phase 3
│   └── financial_agent.py        ← Phase 4
│
└── data/
    ├── contracts/                 ← Phase 1.1.1
    ├── deal_data/                 ← Phase 1.2.1
    └── market_defaults/
        └── market_defaults.json  ← Phase 1.3.1
```
