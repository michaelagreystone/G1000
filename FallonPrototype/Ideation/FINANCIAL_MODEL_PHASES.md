# Fallon Financial Model — Phased Build Plan
> Focused entirely on the financial modeling system.
> Foundation (Phase 0) is already built. Start here at Phase 1.

---

## What This System Does

A user describes a real estate development deal in plain English.
The system extracts the project parameters, retrieves comparable historical deals
and current market assumptions from the vector store, and generates a fully
structured pro forma with every assumption labeled — confirmed, estimated, or
missing. Return metrics are computed and displayed immediately. The full model
exports to Excel with a sensitivity table and an audit trail of every assumption source.

---

## System Architecture

```
User Input (plain English)
        │
        ▼
┌──────────────────────┐
│  PARAMETER EXTRACTOR │  — Claude reads the query, pulls out structured fields
│  (Phase 2)           │    (market, program, unit count, target IRR, etc.)
└──────────┬───────────┘
           │ structured ProjectParameters
           ▼
┌──────────────────────┐
│  CONTEXT RETRIEVER   │  — Pulls two data sources in parallel:
│  (Phase 3)           │    1. Historical deal comps (vector search)
│                      │    2. Market defaults (direct JSON lookup + vector)
└──────────┬───────────┘
           │ formatted context block
           ▼
┌──────────────────────┐
│  PRO FORMA GENERATOR │  — Claude generates a structured JSON pro forma
│  (Phase 4)           │    with labeled assumptions and computed returns
└──────────┬───────────┘
           │ validated pro forma dict
           ▼
┌──────────────────────┐
│  RETURN CALCULATOR   │  — Pure Python DCF cross-checks Claude's numbers
│  (Phase 4.4)         │    Flags discrepancies > 15%
└──────────┬───────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
┌─────────┐  ┌──────────┐
│ STREAMLIT│  │  EXCEL   │
│   UI    │  │  EXPORT  │
│(Phase 6)│  │(Phase 5) │
└─────────┘  └──────────┘
```

---

## Phase 1 — Data Layer

**Goal:** Build the two data sources the model draws from: historical deal data
(what Fallon has actually underwritten) and market defaults (current baseline
assumptions by market and program type). Neither sub-agent can function without this.

---

### Phase 1.1 — Market Defaults JSON

**Issue:** The pro forma generator needs reliable, current baseline assumptions
for every market and program type Fallon operates in. These can't be invented —
they need to be structured, labeled with sources, and easy to update as the
market moves. One wrong assumption (a stale cap rate, an outdated construction
cost) propagates through the entire model and produces a useless output.

**Tasks:**

- [ ] **1.1.1 — Define the full variable set per program type**
  Before writing any JSON, document every variable that a Fallon pro forma
  requires for each program type. Organize by section. This becomes the schema
  that every generated model must conform to:

  **Revenue variables:**
  - Multifamily: `rent_psf_monthly`, `avg_unit_size_sf`, `unit_count`,
    `stabilized_occupancy_pct`, `annual_rent_growth_pct`, `lease_up_months`,
    `other_income_per_unit_monthly` (parking, storage, etc.)
  - Office: `rent_psf_annual_nnn`, `rentable_sf`, `stabilized_occupancy_pct`,
    `lease_up_months`, `free_rent_months`, `ti_allowance_psf`,
    `leasing_commission_pct`
  - Hotel: `adr` (average daily rate), `stabilized_occupancy_pct`,
    `revpar`, `total_keys`, `management_fee_pct`, `ff_and_e_reserve_pct`

  **Cost variables (all program types):**
  - `hard_cost_psf` (construction cost per square foot)
  - `soft_cost_pct_of_hard` (architecture, engineering, permits, legal)
  - `developer_fee_pct_of_total_cost`
  - `contingency_pct_of_hard` (typically 5–10%)
  - `land_cost` (user-provided or estimated $/acre × acreage)
  - `carry_cost_months` (construction duration + lease-up)

  **Financing variables:**
  - `construction_loan_ltc_pct` (loan-to-cost ratio)
  - `construction_loan_rate_pct` (interest rate)
  - `construction_loan_term_months`
  - `equity_split_lp_pct` (LP ownership share)
  - `preferred_return_pct` (LP preferred return before promote)
  - `promote_pct` (GP share of profits above pref)

  **Exit/disposition variables:**
  - `exit_cap_rate_pct` (stabilized NOI / exit value)
  - `exit_sale_cost_pct` (broker fees, transfer taxes — typically 2–3%)
  - `exit_year` (years from construction start)

  **Return metrics (calculated, not input):**
  - `project_irr_levered_pct`
  - `project_irr_unlevered_pct`
  - `lp_irr_pct`
  - `equity_multiple_lp`
  - `profit_on_cost_pct`
  - `development_spread_bps` (yield on cost minus exit cap rate × 100)

- [ ] **1.1.2 — Build `market_defaults.json`**
  Create `FallonPrototype/data/market_defaults/market_defaults.json`.
  Structure: `{market → program_type → variable → {value, unit, source}}`.
  Every leaf is a dict with three keys — `value` (the number), `unit`
  (e.g. "$/sf/month", "%", "months"), and `source` (e.g. "Charlotte broker
  market data, Q4 2025"). This source key flows all the way to the Excel
  export so every assumption is traceable.

  Populate for these market/program combinations at minimum:
  - Charlotte: multifamily, office
  - Nashville: multifamily, office, hotel
  - Boston: multifamily, office
  - national_average: multifamily, office, hotel (fallback if market not found)

  Use publicly available Q4 2025 market data (CBRE, JLL, Marcus & Millichap
  reports) as the basis. These are placeholder values until Fallon replaces
  them with broker-confirmed numbers.

- [ ] **1.1.3 — Add a `last_updated` and `data_quality` field to each market block**
  At the top level of each market dict (not each variable), add:
  ```json
  "charlotte": {
    "_meta": {
      "last_updated": "2025-12-01",
      "data_quality": "estimated",
      "update_notes": "Based on public CBRE Q3 2025 report. Replace with broker confirmation."
    },
    "multifamily": { ... }
  }
  ```
  The `data_quality` field is either `"estimated"` (public data) or
  `"broker_confirmed"` (manually updated by Fallon's team). This propagates
  to the `label` field on every generated assumption so the model self-documents
  its own reliability.

- [ ] **1.1.4 — Write a validation script for the JSON**
  Create `FallonPrototype/shared/validate_defaults.py`. Run it after any
  edit to `market_defaults.json`. It checks: (a) every required variable
  from the Phase 1.1.1 list is present for each market/program combination,
  (b) no value is `null` without a note explaining why, (c) all percentage
  values are in decimal range 0–100 (not 0–1), and (d) all `source` strings
  are non-empty. Print a pass/fail report with specific missing fields. This
  script is the guard rail — run it before every ingestion.

---

### Phase 1.2 — Historical Deal Data

**Issue:** Market defaults give the model current benchmarks. Historical deal
data gives it Fallon-specific context — what returns they've actually achieved,
what assumptions held up and which didn't, how their deals are structured
compared to market. Without this layer, the model is generic. With it, the
model reflects Fallon's actual institutional knowledge.

**Tasks:**

- [ ] **1.2.1 — Create sample deal data files**
  Populate `FallonPrototype/data/deal_data/` with representative text files
  for each deal type. These are the training corpus — realistic deal memos
  written in the style Fallon actually uses. Create at minimum:

  `nashville_mixed_use_overview.txt` — Describe a 300-unit multifamily +
  20,000sf retail mixed-use project. Include: site description, business plan
  rationale, market selection logic, key assumptions used at underwriting,
  final return metrics achieved, and lessons learned (what changed from
  underwriting to exit).

  `charlotte_multifamily_overview.txt` — 180-unit multifamily in South End
  Charlotte. Include: underwriting assumptions, construction cost overruns
  encountered, lease-up timeline vs projection, exit cap rate achieved vs
  assumed, final LP IRR delivered.

  `boston_office_overview.txt` — 80,000sf Class A office building in Seaport.
  Include: business plan rationale for office in post-COVID environment,
  pre-lease requirement met before construction start, tenant improvement
  costs, financing terms, return on cost achieved.

  `fanpier_residential_overview.txt` — Condo project in Seaport (reference
  to the project Danny mentioned). Include: merchant developer model for
  condos (sell units as delivered vs rent), pricing per unit, construction
  timeline, gross margin on sellout.

  Each file should be 400–600 words. Use realistic numbers. These are
  the documents the Financial Model sub-agent retrieves when generating
  a new comparable deal.

- [ ] **1.2.2 — Define metadata schema for deal data chunks**
  Every chunk ingested from deal data files gets metadata that the retrieval
  system can filter on. Define the required fields:
  ```python
  {
    "source": "nashville_mixed_use_overview.txt",
    "deal_type": "mixed_use",         # multifamily | office | hotel | mixed_use | condo
    "market": "nashville",            # charlotte | nashville | boston | other
    "deal_status": "completed",       # completed | active | underwriting
    "approx_year": "2023",            # year of delivery or underwriting
    "program_mix": "multifamily,retail",
    "chunk_index": 0,
    "total_chunks": 5
  }
  ```
  This metadata enables the retrieval function to filter by market or deal
  type when the user specifies one, rather than returning the most semantically
  similar chunk regardless of relevance.

- [ ] **1.2.3 — Build `ingest_deal_data.py`**
  Create `FallonPrototype/shared/ingest_deal_data.py`. The ingestion script:

  1. Reads every `.txt` file in `data/deal_data/`
  2. Determines metadata from the filename (parse market and deal_type from
     the naming convention `{market}_{deal_type}_overview.txt`)
  3. Splits text into chunks using `RecursiveCharacterTextSplitter` with
     `chunk_size=1200` and `chunk_overlap=200`. Deal memo prose is denser
     and more context-dependent than contracts — larger chunks preserve
     the narrative flow that makes comps useful
  4. Generates chunk IDs: `"{filename_without_ext}_{chunk_index:03d}"`
  5. Calls `add_documents("fallon_deal_data", ...)` with all chunks and metadata
  6. Prints a summary and exits

  Make it runnable standalone: `python -m FallonPrototype.shared.ingest_deal_data`

- [ ] **1.2.4 — Validate ingestion with a relevance test**
  After running ingestion, open a Python REPL and run:
  ```python
  from FallonPrototype.shared.vector_store import query_collection
  results = query_collection("fallon_deal_data",
                              "Nashville multifamily returns and cap rate assumptions",
                              n_results=3)
  for r in results:
      print(r["metadata"]["source"], r["distance"])
      print(r["text"][:200])
      print()
  ```
  The top result should be from `nashville_mixed_use_overview.txt` with
  distance < 0.35. If it isn't, the chunk size or the text content needs
  adjustment. Fix before moving to Phase 2.

---

### Phase 1.3 — Market Defaults Ingestion

**Issue:** Market defaults are stored as JSON for precise direct lookup, but
also need to be embedded as text in the vector store so the Financial Model
sub-agent can retrieve them alongside deal comps in the same query. The vector
representation allows natural language queries like "what are Nashville hotel
assumptions?" to surface the right defaults even if the user doesn't type the
exact market name.

**Tasks:**

- [ ] **1.3.1 — Build `ingest_market_defaults.py`**
  Create `FallonPrototype/shared/ingest_market_defaults.py`. For each
  market/program combination in `market_defaults.json`, convert it into a
  human-readable text block and ingest it into `fallon_market_defaults`.

  Convert format example:
  ```
  Charlotte multifamily development assumptions (Q4 2025, data quality: estimated):
  Monthly rent: $1.95/sf/month | Construction cost: $275/sf | Exit cap rate: 5.25% |
  Stabilized occupancy: 94% | Lease-up period: 18 months | Soft costs: 22% of hard |
  Developer fee: 4% of total cost | Construction loan LTC: 65% at 7.75% |
  Target LP IRR: 15% | Target equity multiple: 1.85x
  Source: Charlotte broker market data, Q4 2025
  ```

  Metadata for each record:
  ```python
  {"market": "charlotte", "program_type": "multifamily",
   "data_quality": "estimated", "last_updated": "2025-12-01"}
  ```

  ID format: `"defaults_{market}_{program_type}"` — one record per combination.
  Since there's only one defaults record per market/program, these will always
  be upserted (replaced) when the JSON is updated, keeping the vector store current.

- [ ] **1.3.2 — Create a combined ingestion runner**
  Create `FallonPrototype/shared/run_all_ingestion.py` that runs both
  `ingest_deal_data.py` and `ingest_market_defaults.py` in sequence and
  prints a final status summary:
  ```
  Ingestion complete:
    fallon_deal_data:         22 chunks across 4 files
    fallon_market_defaults:   9 records (3 markets × 3 program types)
  ```
  This is the single command to run after adding new deal files or updating
  market defaults. The Streamlit sidebar "Re-index" button calls this.

---

## Phase 2 — Parameter Extractor

**Goal:** Convert a plain-English project description into a structured
`ProjectParameters` object. This is the first thing that runs on every user
query. If extraction is wrong, every downstream step is wrong.

---

### Phase 2.1 — Define the Schema

**Issue:** The schema must capture everything the model needs, handle
everything the user might omit, and clearly distinguish between fields the
user provided vs. fields that will be filled with defaults.

**Tasks:**

- [ ] **2.1.1 — Build the `ProjectParameters` dataclass**
  Create `FallonPrototype/agents/financial_agent.py`. Define:
  ```python
  from dataclasses import dataclass, field

  @dataclass
  class ProjectParameters:
      # Required — model cannot generate without these
      market: str | None = None          # "charlotte" | "nashville" | "boston" | "other"
      program_type: str | None = None    # "multifamily" | "office" | "hotel" |
                                         # "mixed_use" | "condo"

      # Dimensional inputs — used to calculate revenue and costs
      unit_count: int | None = None      # residential units
      rentable_sf: int | None = None     # office/retail square footage
      total_gfa_sf: int | None = None    # gross floor area (all uses)
      land_cost: float | None = None     # total land cost in dollars
      acreage: float | None = None       # site size

      # Return targets — user's goals for the deal
      target_lp_irr_pct: float | None = None
      target_equity_multiple: float | None = None

      # Timing
      construction_start: str | None = None  # free text: "Q3 2026", "next year"
      construction_duration_months: int | None = None

      # Program mix (for mixed_use)
      mixed_use_components: list[str] = field(default_factory=list)
                                         # e.g. ["multifamily", "retail", "hotel"]

      # Any additional context from the query that doesn't fit above
      notes: str = ""
  ```

- [ ] **2.1.2 — Define required vs. optional fields**
  Document clearly which fields are required for generation to proceed and
  which can be defaulted:

  **Hard required** (generation fails without these — ask user):
  - `market`
  - `program_type`

  **Soft required** (model works with defaults, but accuracy improves with real values):
  - `unit_count` or `rentable_sf` (at least one dimensional input)
  - `land_cost` or `acreage`

  **Optional** (pure defaults used, labeled "estimated"):
  - All return targets, timing, mixed-use components

  This distinction drives the clarification prompt logic in Phase 2.3.

---

### Phase 2.2 — Claude-Powered Extraction

**Issue:** Users describe deals in many ways. "Build me a model for 200 units
in Charlotte" and "I'm looking at a 200-unit apartment project in the South End
Charlotte, targeting a 14% IRR" both need to produce the same structured output.
Regex won't catch the variation — Claude does.

**Tasks:**

- [ ] **2.2.1 — Write the extraction system prompt**
  The system prompt must be extremely specific about output format. Claude
  tends to add explanation — the prompt must prevent this:
  ```
  You are a real estate financial analyst assistant. Extract project parameters
  from the user's description and return ONLY a valid JSON object with the
  following fields. Use null for any field not mentioned. Do not add explanation,
  commentary, or markdown formatting — return only the raw JSON object.

  Required fields:
  {
    "market": string or null,
    "program_type": string or null,
    "unit_count": integer or null,
    "rentable_sf": integer or null,
    "total_gfa_sf": integer or null,
    "land_cost": float or null,
    "acreage": float or null,
    "target_lp_irr_pct": float or null,
    "target_equity_multiple": float or null,
    "construction_start": string or null,
    "construction_duration_months": integer or null,
    "mixed_use_components": array of strings or [],
    "notes": string (capture any project context not in the above fields)
  }

  Normalize these values:
  - market must be one of: "charlotte", "nashville", "boston", "other"
  - program_type must be one of: "multifamily", "office", "hotel", "mixed_use", "condo"
  - All percentages as floats 0–100 (14% → 14.0, not 0.14)
  - unit_count and rentable_sf as integers, not strings
  ```

- [ ] **2.2.2 — Build `extract_parameters()`**
  In `financial_agent.py`, write:
  ```python
  def extract_parameters(query: str) -> ProjectParameters
  ```
  Steps:
  1. Call `call_claude(EXTRACTION_SYSTEM_PROMPT, query, max_tokens=512)`
  2. Strip any accidental markdown fences (` ```json ` etc.) from the response
  3. Parse with `json.loads()` — wrap in try/except
  4. Hydrate into `ProjectParameters` dataclass
  5. On JSON parse failure: log the raw response and return a
     `ProjectParameters` with all fields null. The clarification handler
     in Phase 2.3 will catch this and ask the user to re-state the request.

- [ ] **2.2.3 — Add a normalization pass after extraction**
  Write `normalize_parameters(params: ProjectParameters) -> ProjectParameters`
  that applies light corrections after extraction:
  - Lowercase and strip whitespace from `market` and `program_type`
  - If `program_type` is "apartment" or "residential", map to "multifamily"
  - If `program_type` is "commercial", map to "office"
  - If `unit_count` is provided but `total_gfa_sf` is not, estimate:
    `total_gfa_sf = unit_count * 900` (avg unit size 900sf as placeholder)
  - If `acreage` is provided but `land_cost` is not, leave null
    (the model will mark it as "missing — user input required")
  Return the normalized params.

- [ ] **2.2.4 — Test extraction against 10 varied inputs**
  Create `FallonPrototype/tests/test_extraction.py`. Write 10 test cases
  ranging from minimal to detailed, and assert the correct fields are populated:
  ```python
  test_cases = [
    ("200 units in Charlotte",
     {"market": "charlotte", "unit_count": 200, "program_type": "multifamily"}),

    ("mixed-use project in Nashville, hotel and apartments, 300 keys and 150 units",
     {"market": "nashville", "program_type": "mixed_use",
      "mixed_use_components": ["hotel", "multifamily"]}),

    ("80k sf office building in Boston Seaport targeting 15% IRR",
     {"market": "boston", "program_type": "office",
      "rentable_sf": 80000, "target_lp_irr_pct": 15.0}),
    # ... 7 more cases
  ]
  ```
  All 10 must pass before moving to Phase 2.3. If any fail, refine the
  extraction prompt — do not patch with post-processing hacks.

---

### Phase 2.3 — Missing Parameter Handler

**Issue:** A model without a market or program type is meaningless. The
system needs to ask exactly what's missing — not a generic "please provide
more info" — and accept the answer without requiring the user to re-type
their entire query.

**Tasks:**

- [ ] **2.3.1 — Build `check_missing_parameters()`**
  Write `check_missing_parameters(params: ProjectParameters) -> list[str]`
  that returns a list of human-readable gap descriptions. Example returns:
  - `["market (Charlotte / Nashville / Boston)"]`
  - `["program type (multifamily / office / hotel / condo / mixed-use)",
     "unit count or square footage"]`
  - `[]` (empty list = all required fields present, proceed to generation)

- [ ] **2.3.2 — Build the clarification message formatter**
  Write `format_clarification_message(missing: list[str]) -> str` that
  produces a specific, actionable message. Example:
  ```
  "To generate your model I need a couple more details:
   • Market: Charlotte, Nashville, or Boston?
   • Program type: multifamily, office, hotel, condo, or mixed-use?
  Reply with just those two answers and I'll build the model."
  ```
  This message is what the Streamlit UI displays when required fields are
  missing. The user's reply is then merged with the original query and
  re-run through extraction. Never show a generic "invalid input" error.

- [ ] **2.3.3 — Build the parameter merge function**
  Write `merge_clarification(original_params: ProjectParameters,
  clarification_text: str) -> ProjectParameters` that:
  1. Re-runs extraction on the clarification text alone
  2. Copies any non-null fields from the clarification result into
     `original_params`, overwriting only null fields
  3. Returns the merged params

  This preserves everything the user provided in the first message and
  only fills in what was missing.

---

## Phase 3 — Context Retriever

**Goal:** Before Claude generates the pro forma, it needs two things: what
Fallon has done in comparable situations, and what the current market looks
like. Phase 3 retrieves both and formats them into a single context block
that Claude can reason over.

---

### Phase 3.1 — Deal Comps Retrieval

**Issue:** The retrieval query needs to be constructed from the extracted
parameters — not passed as raw user text. A user might say "200 units in
Charlotte" but the retrieval query should be "Charlotte multifamily residential
development comparable deal returns assumptions" — a query crafted to surface
the most useful deal memo chunks.

**Tasks:**

- [ ] **3.1.1 — Build the retrieval query constructor**
  Write `build_deal_query(params: ProjectParameters) -> str` that constructs
  a targeted retrieval query from the parameters. Examples:
  - `{market: "charlotte", program_type: "multifamily"}` →
    `"Charlotte multifamily residential development pro forma IRR returns assumptions"`
  - `{market: "nashville", program_type: "mixed_use"}` →
    `"Nashville mixed-use development hotel residential pro forma returns underwriting"`
  - `{market: "boston", program_type: "office"}` →
    `"Boston Class A office development pro forma lease-up construction cost returns"`

  The query string includes the market, program type, and high-value terms
  ("pro forma", "IRR", "returns", "assumptions") to bias retrieval toward
  financial content rather than narrative description.

- [ ] **3.1.2 — Build `retrieve_deal_comps()`**
  Write `retrieve_deal_comps(params: ProjectParameters) -> list[dict]` that:
  1. Builds the retrieval query using `build_deal_query()`
  2. Calls `query_collection("fallon_deal_data", query, n_results=4)`
  3. If `params.market` is not None, also calls with a metadata filter:
     `where={"market": {"$eq": params.market}}` and takes up to 2 results
  4. Merges both result sets, deduplicates by chunk ID, keeps top 4 by distance
  5. Filters out any chunk with `relevance == "low"` — low-relevance comps
     add noise and can mislead the model
  6. Returns the final list

  The two-pass approach (semantic + metadata-filtered) ensures both
  relevance and market specificity. If the metadata-filtered pass returns
  nothing (market not in the corpus), the semantic results carry the full load.

- [ ] **3.1.3 — Handle the empty corpus case**
  If `fallon_deal_data` collection has 0 documents, `retrieve_deal_comps()`
  should return an empty list rather than raising an error. The generator
  will handle this by noting "No historical Fallon comps available for this
  market/program. Using market defaults only." in the pro forma notes field.
  This is not a failure — it's a known state during initial setup.

---

### Phase 3.2 — Market Defaults Retrieval

**Issue:** The generator needs defaults in two formats: (1) as a structured
dict for exact numeric injection into the pro forma, and (2) as text for
Claude to reason over. Both are required because Claude needs context to make
intelligent adjustments, not just raw numbers to paste in.

**Tasks:**

- [ ] **3.2.1 — Build the direct defaults lookup**
  Write `get_defaults_for_params(params: ProjectParameters) -> dict | None`
  that calls `get_market_defaults(params.market, params.program_type)` from
  `vector_store.py`. Handle the mixed_use case: if `program_type == "mixed_use"`,
  retrieve defaults for each component in `mixed_use_components` and merge
  them, with office/hotel/retail components using their own program-type
  defaults and multifamily using multifamily defaults. Return a combined dict
  labeled with each component's source.

- [ ] **3.2.2 — Build the vector defaults retrieval**
  Write `retrieve_defaults_context(params: ProjectParameters) -> list[dict]`
  that queries the `fallon_market_defaults` collection with a targeted query.
  Use `where={"market": {"$eq": params.market}}` to ensure only the correct
  market's defaults are returned. This gives Claude the text version of the
  defaults for reasoning, alongside the structured dict for number injection.

- [ ] **3.2.3 — Handle the fallback case clearly**
  If `get_market_defaults()` returns a result with `_fallback: True`, the
  structured dict is national averages, not Charlotte/Nashville/Boston specifics.
  In this case, add a warning string to the context: `"WARNING: No market-specific
  defaults available for '{market}'. National averages used. All cost and revenue
  assumptions require local broker verification before use."` This warning
  propagates to the pro forma's `notes` field and to the UI banner.

---

### Phase 3.3 — Context Formatter

**Issue:** Claude's prompt has a finite context window and a finite attention
span. Poorly formatted context — walls of numbers, unlabeled sections,
redundant data — degrades output quality. The formatter is not a cosmetic
concern; it directly affects what the model generates.

**Tasks:**

- [ ] **3.3.1 — Build `format_financial_context()`**
  Write `format_financial_context(deal_comps: list[dict],
  defaults_dict: dict | None, defaults_chunks: list[dict]) -> str`
  that produces a structured, labeled context block. Format:

  ```
  ═══════════════════════════════════════════
  SECTION 1: HISTORICAL FALLON DEAL COMPARABLES
  ═══════════════════════════════════════════

  --- COMPARABLE 1 ---
  Source: nashville_mixed_use_overview.txt | Relevance: high
  [chunk text]

  --- COMPARABLE 2 ---
  Source: charlotte_multifamily_overview.txt | Relevance: medium
  [chunk text]

  ═══════════════════════════════════════════
  SECTION 2: CURRENT MARKET DEFAULTS
  Market: Charlotte | Program: Multifamily | Data Quality: estimated
  Last Updated: 2025-12-01
  ═══════════════════════════════════════════

  Monthly rent:            $1.95/sf/month  (Source: Charlotte broker data Q4 2025)
  Construction cost:       $275/sf          (Source: Charlotte broker data Q4 2025)
  Exit cap rate:           5.25%            (Source: Charlotte broker data Q4 2025)
  Stabilized occupancy:    94%              ...
  [etc.]

  ═══════════════════════════════════════════
  SECTION 3: RETRIEVED DEFAULTS CONTEXT
  ═══════════════════════════════════════════
  [vector-retrieved defaults text chunks for additional context]
  ```

  Total context length should not exceed 3,000 tokens. If deal comps push
  it over, truncate to the highest-relevance chunks. Never truncate Section 2
  (the structured defaults) — that's what the model depends on most.

- [ ] **3.3.2 — Add a context quality summary line**
  At the bottom of the formatted context, add a one-line summary:
  ```
  Context quality: 3 deal comps (2 high, 1 medium relevance) |
  Market defaults: Charlotte multifamily (estimated) | Fallback: No
  ```
  This line is included in the Claude prompt so the model can calibrate
  its own confidence in the output.

---

## Phase 4 — Pro Forma Generator

**Goal:** The core of the system. Claude receives the formatted context +
user parameters and generates a complete, structured pro forma JSON. Every
assumption is labeled. Return metrics are computed and cross-checked by
a pure Python calculator.

---

### Phase 4.1 — Pro Forma Output Schema

**Issue:** If Claude generates a different JSON structure every time, the UI
and Excel exporter break. The schema must be exact, documented, and enforced
by the system prompt and a post-generation validator.

**Tasks:**

- [ ] **4.1.1 — Define the complete pro forma schema**
  In `financial_agent.py`, define `PRO_FORMA_SCHEMA` as a module-level dict
  that documents the exact expected output structure. Every leaf value follows
  this pattern:
  ```python
  {
    "value": float | None,
    "unit": str,            # "$/sf/month", "%", "months", "$", "x", "bps"
    "label": str,           # "confirmed" | "estimated" | "calculated" | "missing"
    "source": str           # source string, formula, or "user-provided"
  }
  ```

  Full schema (five sections):
  ```python
  {
    "project_summary": {
      "deal_name": ...,
      "market": ...,
      "program_type": ...,
      "total_gfa_sf": ...,
      "unit_count": ...,           # null for office/hotel
      "rentable_sf": ...,          # null for residential
      "construction_start": ...,
      "construction_duration_months": ...,
      "total_keys": ...,           # null unless hotel
      "notes": ...                 # plain text, no value/unit/label/source wrapper
    },
    "revenue_assumptions": {
      "rent_psf_monthly": ...,     # multifamily
      "rent_psf_annual_nnn": ...,  # office
      "adr": ...,                  # hotel
      "stabilized_occupancy_pct": ...,
      "lease_up_months": ...,
      "annual_rent_growth_pct": ...,
      "other_income_per_unit_monthly": ...  # null if not applicable
    },
    "cost_assumptions": {
      "land_cost_total": ...,
      "hard_cost_psf": ...,
      "hard_cost_total": ...,       # calculated: hard_cost_psf × total_gfa_sf
      "soft_cost_pct_of_hard": ...,
      "soft_cost_total": ...,       # calculated
      "developer_fee_pct": ...,
      "developer_fee_total": ...,   # calculated
      "contingency_pct": ...,
      "contingency_total": ...,     # calculated
      "total_project_cost": ...     # calculated: all costs summed
    },
    "financing_assumptions": {
      "construction_loan_ltc_pct": ...,
      "construction_loan_amount": ...,  # calculated: ltc × total_project_cost
      "construction_loan_rate_pct": ...,
      "carry_cost_total": ...,          # calculated: loan × rate × (term/12)
      "equity_required": ...,           # calculated: total_cost − loan
      "lp_equity_pct": ...,
      "lp_equity_amount": ...,          # calculated
      "gp_equity_pct": ...,
      "gp_equity_amount": ...           # calculated
    },
    "return_metrics": {
      "stabilized_noi": ...,            # calculated
      "gross_exit_value": ...,          # calculated: noi / cap_rate
      "net_exit_value": ...,            # calculated: gross − sale_costs
      "total_profit": ...,              # calculated: net_exit − total_cost
      "profit_on_cost_pct": ...,        # calculated: profit / total_cost × 100
      "development_spread_bps": ...,    # calculated: (yield_on_cost − cap_rate) × 10000
      "project_irr_levered_pct": ...,   # estimated by Claude, cross-checked by calculator
      "equity_multiple_lp": ...,        # estimated by Claude, cross-checked by calculator
      "lp_irr_pct": ...                 # estimated by Claude
    }
  }
  ```

---

### Phase 4.2 — System Prompt Engineering

**Issue:** The system prompt for generation is the most important piece of
engineering in the entire project. It determines whether outputs are
structured, labeled, grounded in context, and reliable — or generic,
hallucinated, and dangerously wrong.

**Tasks:**

- [ ] **4.2.1 — Write `GENERATION_SYSTEM_PROMPT`**
  Define as a module-level constant in `financial_agent.py`. The prompt must:

  **Set the role precisely:**
  ```
  You are a real estate financial analyst for The Fallon Company, a merchant
  developer based in Boston with a $6B development pipeline. Your task is to
  generate a complete development pro forma in JSON format based on the project
  parameters and market context provided.
  ```

  **Ground the output in the provided context:**
  ```
  Use ONLY the values provided in the market defaults and historical deal
  comparables sections of the context. Do not use general knowledge or
  external benchmarks. If a value is not in the context and cannot be
  calculated from values that are, set "value" to null and "label" to
  "missing — broker input required".
  ```

  **Enforce the label taxonomy strictly:**
  ```
  Every numeric value must have a "label" field set to exactly one of:
  - "confirmed"  : value was explicitly stated by the user
  - "estimated"  : value sourced from the provided market defaults
  - "calculated" : value derived mathematically from other values in this model
  - "missing"    : value is required but not available in context or user input
  ```

  **Enforce the output format:**
  ```
  Return ONLY the JSON object. No explanation before or after. No markdown
  code fences. No commentary. The entire response must be valid JSON that
  can be parsed by json.loads() without modification.
  ```

  **Set return metric expectations:**
  ```
  For "project_irr_levered_pct" and "equity_multiple_lp": use the provided
  market defaults as targets if the user specified none. If the assumptions
  imply returns significantly above or below market, note this in the
  project_summary.notes field rather than adjusting assumptions silently.
  ```

- [ ] **4.2.2 — Build the user message template**
  Write `build_generation_message(params: ProjectParameters,
  context: str) -> str` that combines the extracted parameters and
  formatted context into the user message:
  ```
  PROJECT PARAMETERS:
  Market: {market}
  Program type: {program_type}
  Unit count: {unit_count or "not specified"}
  Total GFA: {total_gfa_sf or "not specified"}
  Land cost: {land_cost or "not specified"}
  Target LP IRR: {target_lp_irr_pct or "use market default"}
  Target equity multiple: {target_equity_multiple or "use market default"}
  Construction start: {construction_start or "not specified"}
  Additional notes: {notes or "none"}

  CONTEXT:
  {context}

  Generate the complete pro forma JSON for this project.
  ```

---

### Phase 4.3 — JSON Parsing & Validation

**Issue:** Claude occasionally adds explanation before or after JSON,
wraps it in markdown fences, or produces structurally invalid JSON for
complex schemas. The parser must handle all of these failure modes
without crashing.

**Tasks:**

- [ ] **4.3.1 — Build a robust JSON extractor**
  Write `extract_json_from_response(response: str) -> dict | None` that:
  1. Strips leading/trailing whitespace
  2. If the string starts with ` ```json `, strips the fence markers
  3. Finds the first `{` and last `}` and extracts the substring
     (handles cases where Claude adds a sentence before the JSON)
  4. Runs `json.loads()` on the extracted substring
  5. Returns the parsed dict on success, `None` on failure
  6. On failure: logs the raw response to a file
     `FallonPrototype/logs/parse_failures.jsonl` for debugging

- [ ] **4.3.2 — Build a schema conformance validator**
  Write `validate_pro_forma(data: dict) -> tuple[bool, list[str]]` that
  checks the parsed JSON against the schema from Phase 4.1.1. Returns
  `(True, [])` on pass, `(False, [list of missing/malformed fields])` on fail.

  Checks to run:
  - All five top-level sections are present
  - Every numeric value is a dict with `value`, `unit`, `label`, `source` keys
  - No `label` field contains a value outside the four allowed values
  - `return_metrics` section is present and non-empty
  - `total_project_cost` is present and has a numeric value (not null)

  If validation fails, log the failure and return a partial pro forma with
  a warning note rather than crashing. A partial model is better than no model.

- [ ] **4.3.3 — Build the retry logic**
  If `extract_json_from_response()` returns `None` (parse failure),
  make one retry with a simplified prompt: append to the user message
  `"Your previous response could not be parsed as JSON. Return ONLY the
  JSON object with no other text."` and call Claude again. If the retry
  also fails, return an error `AgentResponse` with a clear message.
  Never retry more than once — two failures means a structural prompt issue
  that needs manual debugging.

---

### Phase 4.4 — Return Metrics Calculator

**Issue:** Claude estimates IRR and equity multiple, but it's not a
spreadsheet. It can get the direction right but not the precision. A pure
Python calculator running the same assumptions as a simplified DCF gives
a cross-check. If the two diverge by more than 15%, there's likely an
error in the assumptions that Claude didn't catch.

**Tasks:**

- [ ] **4.4.1 — Build the core calculator**
  Create `FallonPrototype/shared/return_calculator.py`.
  Write `compute_returns(pro_forma: dict) -> dict` that extracts the
  key numbers from the generated pro forma and runs simplified return math:

  ```python
  def compute_returns(pro_forma: dict) -> dict:
      costs = pro_forma["cost_assumptions"]
      financing = pro_forma["financing_assumptions"]
      revenue = pro_forma["revenue_assumptions"]
      summary = pro_forma["project_summary"]

      total_cost = _val(costs, "total_project_cost")
      equity = _val(financing, "equity_required")
      lp_equity = _val(financing, "lp_equity_amount")

      # Simplified exit value
      noi = _estimate_noi(revenue, summary)
      cap_rate = _val(pro_forma.get("exit_assumptions", {}), "exit_cap_rate_pct", 5.25) / 100
      gross_exit = noi / cap_rate if cap_rate > 0 else None

      # Profit
      sale_costs = gross_exit * 0.025 if gross_exit else None  # 2.5% transaction costs
      net_exit = gross_exit - sale_costs if gross_exit else None
      total_profit = net_exit - total_cost if (net_exit and total_cost) else None

      # Simplified IRR (approximate — not a full DCF)
      hold_years = _val(summary, "construction_duration_months", 24) / 12 + 1.5
      if equity and total_profit and hold_years > 0:
          equity_multiple = (equity + (total_profit * lp_equity / equity)) / lp_equity \
                            if lp_equity else None
          # Approximate IRR: (multiple ^ (1/years)) - 1
          irr_approx = ((equity_multiple ** (1 / hold_years)) - 1) * 100 \
                       if equity_multiple else None
      else:
          equity_multiple = None
          irr_approx = None

      return {
          "calc_noi": noi,
          "calc_gross_exit_value": gross_exit,
          "calc_total_profit": total_profit,
          "calc_profit_on_cost_pct": (total_profit / total_cost * 100)
                                     if (total_profit and total_cost) else None,
          "calc_equity_multiple_approx": equity_multiple,
          "calc_irr_approx_pct": irr_approx,
      }
  ```

- [ ] **4.4.2 — Build the discrepancy check**
  Write `check_return_discrepancy(pro_forma: dict,
  calc_results: dict) -> list[str]` that compares:
  - Claude's `profit_on_cost_pct` vs `calc_profit_on_cost_pct`
  - Claude's `equity_multiple_lp` vs `calc_equity_multiple_approx`
  - Claude's `project_irr_levered_pct` vs `calc_irr_approx_pct`

  For each metric where the difference exceeds 15%: add a warning string
  to the returned list. Example:
  ```
  "WARNING: Equity multiple discrepancy — model shows 2.1x, calculator
  estimates 1.6x. Review construction cost or exit cap rate assumptions."
  ```
  These warnings appear in the Streamlit UI as yellow banners above the
  return metrics section.

- [ ] **4.4.3 — Add the `_val()` helper**
  Write `_val(section: dict, key: str, default=None)` that safely extracts
  the `value` from a pro forma section field, returning `default` if the
  field is missing, null, or non-numeric. Every accessor in the calculator
  uses this — never direct dict access — to prevent the calculator from
  crashing on partially complete models.

---

### Phase 4.5 — Sensitivity Analysis

**Issue:** The first question any LP or lender asks is "what if assumptions
change?" Cap rates move. Construction costs overrun. A model without
sensitivity analysis is incomplete for Fallon's actual use case.

**Tasks:**

- [ ] **4.5.1 — Define the sensitivity matrix**
  The sensitivity table tests two variables against each other, with three
  scenarios each, producing a 3×3 grid of return outcomes. Default variables:
  - Rows: Exit cap rate (base − 50bps, base, base + 50bps)
  - Columns: Construction cost (base − 10%, base, base + 10%)
  - Cell value: Levered IRR (%)

  The 3×3 format is deliberately constrained — simple enough to be readable,
  comprehensive enough to show the range that matters most.

- [ ] **4.5.2 — Build `compute_sensitivity_table()`**
  Write `compute_sensitivity_table(pro_forma: dict) -> dict` that:
  1. Extracts the base cap rate and base construction cost from the pro forma
  2. Defines the 9 scenario combinations
  3. For each scenario: copies the pro forma, overrides the two variables,
     runs `compute_returns()`, extracts IRR
  4. Returns a dict:
     ```python
     {
       "row_label": "Exit Cap Rate",
       "col_label": "Construction Cost",
       "rows": ["4.75%", "5.25%", "5.75%"],
       "cols": ["-10%", "Base", "+10%"],
       "values": [[irr_1_1, irr_1_2, irr_1_3],
                  [irr_2_1, irr_2_2, irr_2_3],
                  [irr_3_1, irr_3_2, irr_3_3]]
     }
     ```
  5. Marks the base-base cell (center) as the "current" scenario

- [ ] **4.5.3 — Add a "deal works / doesn't work" signal to each cell**
  Using the LP's target IRR from `params.target_lp_irr_pct` (or the market
  default if none was provided), mark each cell as:
  - `"green"` if IRR ≥ target
  - `"yellow"` if within 200bps below target
  - `"red"` if more than 200bps below target
  This color coding passes through to both the Streamlit display and the
  Excel export.

---

### Phase 4.6 — `financial_agent.run()`

**Issue:** All the components need to connect into a single callable function
that the orchestrator (or UI) calls and gets back a complete, validated result.

**Tasks:**

- [ ] **4.6.1 — Build the main `run()` function**
  Write `run(query: str) -> AgentResponse` that orchestrates the full pipeline:
  ```python
  def run(query: str) -> AgentResponse:
      # 1. Extract and normalize parameters
      params = normalize_parameters(extract_parameters(query))

      # 2. Check for missing required params
      missing = check_missing_parameters(params)
      if missing:
          return AgentResponse(
              intent="FINANCIAL_MODEL",
              answer=format_clarification_message(missing),
              sources=[], raw_chunks=[], confidence="low",
              export_data=None, needs_clarification=True
          )

      # 3. Retrieve context (both passes in parallel via threading)
      deal_comps = retrieve_deal_comps(params)
      defaults_dict = get_defaults_for_params(params)
      defaults_chunks = retrieve_defaults_context(params)

      # 4. Format context
      context = format_financial_context(deal_comps, defaults_dict, defaults_chunks)

      # 5. Build generation message and call Claude
      message = build_generation_message(params, context)
      raw_response = call_claude(GENERATION_SYSTEM_PROMPT, message, max_tokens=4096)

      # 6. Parse and validate
      pro_forma = extract_json_from_response(raw_response)
      if pro_forma is None:
          # One retry
          raw_response = call_claude(GENERATION_SYSTEM_PROMPT,
                                     message + "\nReturn ONLY the JSON object.",
                                     max_tokens=4096)
          pro_forma = extract_json_from_response(raw_response)

      if pro_forma is None:
          return AgentResponse(intent="FINANCIAL_MODEL",
                               answer="ERROR: Could not generate a valid pro forma. "
                                      "Please rephrase your request.",
                               sources=[], raw_chunks=[], confidence="low",
                               export_data=None)

      # 7. Cross-check returns
      calc_results = compute_returns(pro_forma)
      warnings = check_return_discrepancy(pro_forma, calc_results)

      # 8. Compute sensitivity table
      sensitivity = compute_sensitivity_table(pro_forma)

      # 9. Determine confidence
      has_high_comps = any(c["relevance"] == "high" for c in deal_comps)
      has_market_data = defaults_dict is not None and not defaults_dict.get("_fallback")
      confidence = "high" if (has_high_comps and has_market_data) \
                   else "medium" if (has_market_data) else "low"

      # 10. Build plain-English summary for the answer field
      answer = _build_answer_summary(pro_forma, calc_results, warnings)

      return AgentResponse(
          intent="FINANCIAL_MODEL",
          answer=answer,
          sources=[c["metadata"]["source"] for c in deal_comps],
          raw_chunks=deal_comps,
          confidence=confidence,
          export_data={"pro_forma": pro_forma,
                       "sensitivity": sensitivity,
                       "calc_results": calc_results,
                       "warnings": warnings}
      )
  ```

- [ ] **4.6.2 — Build `_build_answer_summary()`**
  Write `_build_answer_summary(pro_forma, calc_results, warnings) -> str` that
  produces a 3–5 sentence plain-English summary of the model. Example:
  ```
  Your Charlotte multifamily deal (200 units, 180,000sf GFA) projects a
  levered LP IRR of 15.8% and 1.92x equity multiple on a total project cost
  of $68.4M. Construction cost is estimated at $275/sf ($49.5M hard cost)
  with 22% soft costs and a 4% developer fee. Exit is modeled at a 5.25% cap
  rate after 18 months of lease-up. All revenue and cost assumptions are
  estimated from Charlotte multifamily market data — review with your broker
  before committing to an underwrite.
  ```

---

## Phase 5 — Excel Export

**Goal:** A professionally formatted Excel workbook that Fallon's analysts
can open, edit, and send to LPs — not a raw data dump.

---

### Phase 5.1 — Workbook Structure

**Tasks:**

- [ ] **5.1.1 — Define the sheet layout**
  Six sheets in order:
  1. `Summary` — headline metrics (IRR, multiple, profit-on-cost) in large
     font at the top, project parameters below, one-paragraph description
  2. `Revenue` — all revenue assumption rows with value/unit/label/source columns
  3. `Costs` — hard cost, soft cost, developer fee, contingency, total
  4. `Financing` — loan sizing, equity split, carry costs
  5. `Returns` — full return metrics + sensitivity table
  6. `Assumptions & Sources` — every estimated assumption with its source
     string and a note to verify with broker

- [ ] **5.1.2 — Build `export_pro_forma()`**
  Create `FallonPrototype/shared/excel_export.py`. Write
  `export_pro_forma(export_data: dict, deal_name: str) -> bytes` using `openpyxl`.
  Color coding for assumption rows by label:
  - `"confirmed"` → yellow fill (`FFFF99`)
  - `"estimated"` → light blue fill (`CCE5FF`)
  - `"calculated"` → white (no fill)
  - `"missing"` → light red fill (`FFCCCC`)

  Return the workbook as `io.BytesIO().getvalue()` for Streamlit download.

- [ ] **5.1.3 — Add the sensitivity table to the Returns sheet**
  After the return metrics rows, add a blank row then the 3×3 sensitivity
  table. Use conditional formatting: green/yellow/red background per cell
  based on the deal-works signal from Phase 4.5.3. Label the table clearly:
  `"Sensitivity Analysis: Levered IRR (%) by Exit Cap Rate and Construction Cost"`

- [ ] **5.1.4 — Add column widths, fonts, and borders**
  - Column A (variable name): width 35
  - Column B (value): width 15, right-aligned
  - Column C (unit): width 12
  - Column D (label): width 14
  - Column E (source): width 45
  - Header rows: bold, dark gray background, white text
  - Section headers within sheets: bold, light gray background

---

## Phase 6 — Streamlit UI

**Goal:** A clean single-page interface that feels like a smart analyst
assistant, not a form. The user types, the model generates, everything is
immediately visible and downloadable.

---

### Phase 6.1 — App Shell

**Tasks:**

- [ ] **6.1.1 — Create `FallonPrototype/app.py`**
  Set up:
  - `st.set_page_config(page_title="Fallon Financial Model", layout="wide")`
  - Sidebar: system status (collections indexed, Claude model, session cost)
  - Main area: input at top, results below

- [ ] **6.1.2 — Build the sidebar status panel**
  Display in the sidebar:
  - Collection counts from `get_collection_counts()`
  - Session token usage and estimated cost from `get_session_usage()`
  - "Re-index Data" button that runs `run_all_ingestion.py` as a subprocess
    and shows a spinner while it runs
  - "Clear Session" button that resets session state and token counter

---

### Phase 6.2 — Input & Generation Flow

**Tasks:**

- [ ] **6.2.1 — Build the query input**
  A `st.text_area()` with placeholder text showing 3 example queries:
  ```
  Examples:
  • "200-unit multifamily in Charlotte, targeting 15% IRR"
  • "Mixed-use hotel and apartments in Nashville, 300 keys and 180 units"
  • "80,000sf Class A office in Boston Seaport"
  ```
  A "Generate Model" button submits the query.

- [ ] **6.2.2 — Handle the clarification flow**
  If `response.needs_clarification == True`, display the clarification message
  in a yellow info box and show a second text input labeled "Your answer:".
  On submit, call `merge_clarification()` and re-run `financial_agent.run()`
  with the merged parameters. Never lose the original query context.

- [ ] **6.2.3 — Show a generation spinner**
  While the model runs, show `st.spinner("Building your pro forma...")`.
  Average generation time is 8–15 seconds — the spinner prevents users
  from thinking the app is frozen.

---

### Phase 6.3 — Results Display

**Tasks:**

- [ ] **6.3.1 — Headline metrics**
  At the top of results, display four metric cards using `st.metric()`:
  - LP IRR (%)
  - Equity Multiple (x)
  - Profit on Cost (%)
  - Total Project Cost ($M)
  Include the calculator cross-check values as the `delta` parameter on
  each `st.metric()`. A delta of +0.2% (calc vs model) communicates precision
  without cluttering the display.

- [ ] **6.3.2 — Confidence and warning banners**
  Immediately below metrics:
  - If `confidence == "low"`: red banner — "Low confidence: no market-specific
    data found. All assumptions are national averages. Verify before use."
  - If `confidence == "medium"`: yellow banner — "Medium confidence: market
    defaults used. Confirm rent and cost assumptions with local broker."
  - If `warnings`: yellow banner for each discrepancy warning from the
    calculator check.

- [ ] **6.3.3 — Pro forma tables**
  Display each section as a `st.dataframe()` with columns: Variable, Value,
  Unit, Status. Apply background colors matching the Excel export
  (yellow/blue/white/red by label). Use `st.tabs()` to separate the five
  sections — cleaner than stacking five tables vertically.

- [ ] **6.3.4 — Sensitivity table**
  Below the pro forma tabs, display the 3×3 sensitivity table as a styled
  dataframe with background colors (green/yellow/red per cell). Label it
  clearly. Show the base case cell with a bold border.

- [ ] **6.3.5 — Source expander**
  An `st.expander("View Assumption Sources & Comparable Deals")` showing:
  - Section 1: every estimated assumption with its source string
  - Section 2: deal comps retrieved, with source filename, relevance score,
    and first 200 characters of the chunk text

---

### Phase 6.4 — Adjust Assumptions & Download

**Tasks:**

- [ ] **6.4.1 — Build the adjust assumptions panel**
  After first generation, show an `st.expander("Adjust Key Assumptions")`.
  Inside: `st.number_input()` fields for the 5 most impactful variables:
  - Exit cap rate (%)
  - Construction cost ($/sf)
  - Monthly rent ($/sf)
  - Construction loan rate (%)
  - Lease-up months
  An "Update Returns" button re-runs `compute_returns()` and
  `compute_sensitivity_table()` with the adjusted values and updates the
  headline metrics and sensitivity table in place. No new API call needed —
  this is pure Python recalculation.

- [ ] **6.4.2 — Build the Excel download button**
  After the results display:
  ```python
  excel_bytes = export_pro_forma(response.export_data,
                                  deal_name=f"{params.market}_{params.program_type}")
  st.download_button(
      label="Download Model (.xlsx)",
      data=excel_bytes,
      file_name=f"fallon_{params.market}_{params.program_type}_model.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  )
  ```

---

## Phase 7 — Testing & Validation

**Goal:** Confirm every component works end-to-end before demo.

**Tasks:**

- [ ] **7.1 — Test extraction accuracy**
  Run `test_extraction.py` (Phase 2.2.4). All 10 cases must pass.

- [ ] **7.2 — Test deal comps retrieval**
  Confirm the top result for a Charlotte multifamily query is from the
  Charlotte deal file, not Nashville or Boston.

- [ ] **7.3 — Test generation for three deal types**
  Run full `financial_agent.run()` for:
  1. `"200-unit multifamily in Charlotte"`
  2. `"Nashville mixed-use hotel and apartments, 300 keys and 150 units"`
  3. `"80,000sf office in Boston targeting 15% IRR"`
  For each: confirm valid JSON returned, all five sections present, all
  labels are one of the four allowed values, return metrics are in plausible ranges.

- [ ] **7.4 — Test the calculator cross-check**
  For a known set of assumptions, manually compute the expected IRR and
  verify `compute_returns()` produces a result within 5% of the manual calc.

- [ ] **7.5 — Test the Excel export**
  Download and open the Excel file. Verify: six sheets present, color coding
  correct, sensitivity table populated, Assumptions & Sources tab complete.

- [ ] **7.6 — Test the adjust assumptions flow**
  In the UI, generate a model, then change the exit cap rate from 5.25% to
  6.0% and click Update Returns. Verify the IRR decreases and the sensitivity
  table updates without a new API call.

- [ ] **7.7 — Test the clarification flow**
  Submit `"build me a model"` with no other details. Verify the clarification
  message appears, answer it with `"Charlotte multifamily"`, and confirm the
  full model generates from the merged parameters.

---

## File Structure

```
FallonPrototype/
├── app.py                              ← Phase 6 — Streamlit UI
│
├── shared/
│   ├── claude_client.py                ← Phase 0.2 (built)
│   ├── vector_store.py                 ← Phase 0.3 (built)
│   ├── ingest_deal_data.py             ← Phase 1.2.3
│   ├── ingest_market_defaults.py       ← Phase 1.3.1
│   ├── run_all_ingestion.py            ← Phase 1.3.2
│   ├── validate_defaults.py            ← Phase 1.1.4
│   ├── return_calculator.py            ← Phase 4.4
│   └── excel_export.py                 ← Phase 5.1.2
│
├── agents/
│   └── financial_agent.py              ← Phase 2–4 (all agent logic)
│
├── data/
│   ├── deal_data/                      ← Phase 1.2.1 — deal memo .txt files
│   └── market_defaults/
│       └── market_defaults.json        ← Phase 1.1.2
│
├── tests/
│   └── test_extraction.py              ← Phase 2.2.4
│
└── logs/
    └── parse_failures.jsonl            ← Phase 4.3.1 — auto-created
```
