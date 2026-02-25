# Fallon Financial Model

A RAG-powered development pro forma generator and contract Q&A system for The Fallon Company.

## Features

### Pro Forma Generator
- Generate complete development pro formas from natural language descriptions
- Supports multifamily, office, hotel, and mixed-use projects
- Markets: Charlotte, Nashville, Boston (with national fallback)
- Returns: IRR, equity multiple, profit-on-cost, sensitivity analysis
- Export to professionally formatted Excel workbooks

### Contract Q&A
- Query JV agreements, waterfall structures, and deal terms
- Search across contract provisions and deal precedents
- Answers grounded in actual Fallon documents

## Quick Start

### 1. Install Dependencies
```bash
cd FallonPrototype
pip install -r requirements.txt
```

### 2. Set Up Environment
Create a `.env` file in the project root (`G1000/.env`) with your API key:
```
NVIDIA_API_KEY=your_nvidia_api_key_here
```

### 3. Index the Data
```bash
python -m FallonPrototype.shared.run_all_ingestion
```

### 4. Run the App
```bash
streamlit run FallonPrototype/app.py
```

The app will open at `http://localhost:8501`

## Usage Examples

### Pro Forma Generation
```
"200-unit multifamily in Charlotte, targeting 15% IRR"
"Mixed-use hotel and apartments in Nashville, 300 keys and 180 units"
"80,000sf Class A office in Boston Seaport"
```

### Contract Questions
```
"How does a typical waterfall distribution work?"
"What is a standard LP preferred return for development deals?"
"Explain the GP catch-up provision"
```

## Project Structure

```
FallonPrototype/
├── app.py                    # Streamlit web interface
├── requirements.txt          # Python dependencies
│
├── agents/
│   ├── financial_agent.py    # Pro forma generation
│   └── contract_agent.py     # Contract Q&A
│
├── shared/
│   ├── claude_client.py      # LLM API client
│   ├── vector_store.py       # ChromaDB vector store
│   ├── return_calculator.py  # IRR/returns calculator
│   ├── excel_export.py       # Excel workbook export
│   └── run_all_ingestion.py  # Data ingestion pipeline
│
├── Financial Model/
│   └── data/
│       ├── deal_data/        # Deal memo examples
│       ├── market_defaults/  # Market assumptions JSON
│       ├── market_research/  # CBRE, JLL research
│       └── contract_provisions/  # Contract templates
│
└── tests/                    # Test suite
```

## Data Sources

### Market Defaults
- Charlotte, Nashville, Boston multifamily/office/hotel
- CBRE cap rate surveys (H2 2025)
- JLL construction cost data (2026)
- National averages as fallback

### Deal Examples
- Charlotte South End Multifamily
- Boston Seaport Life Science Office
- Nashville Gulch Hotel Mixed-Use

### Contract Provisions
- JV Waterfall Structures (90/10, tiered promotes)
- LP/GP Agreements
- Construction Contracts
- Commercial Lease Terms

## Configuration

### Model Settings
The system uses NVIDIA NIM API with Kimi K2 model. Configure in `shared/claude_client.py`:
```python
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "moonshotai/kimi-k2-instruct"
```

### Market Defaults
Edit `Financial Model/data/market_defaults/market_defaults.json` to update:
- Rent assumptions
- Construction costs
- Cap rates
- Financing terms

## Testing

Run the full test suite:
```bash
python -m FallonPrototype.tests.test_full_integration
```

## Notes

- All financial assumptions require broker verification
- The system uses estimated market data - confirm with local sources
- Contract answers are for reference only - consult legal counsel for specific deals
